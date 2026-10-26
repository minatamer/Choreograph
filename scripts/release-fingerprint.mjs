import { createHash } from "node:crypto";
import { lstat, readdir, readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const dockerfiles = ["infra/Dockerfile.frontend", "infra/Dockerfile.backend"];
const forbiddenDirectories = new Set([
  ".git", ".runtime", ".venv", "node_modules", ".next", "__pycache__",
  ".pytest_cache", ".ruff_cache",
]);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const forbidden = (path) => path.split("/").some((part) =>
  forbiddenDirectories.has(part) || part.startsWith(".env") || part.endsWith(".egg-info") ||
  /\.(?:pyc|pyo|tsbuildinfo)$/.test(part));

function relativePath(value) {
  if (!value || /[\\\x00-\x1f$'"?]/.test(value) || value.startsWith("/")) {
    throw new Error("Unsupported release input path");
  }
  const path = value.replace(/^(?:\.\/)+/, "").replace(/\/$/, "");
  if (!path || path.split("/").some((part) => part === ".." || part === "." || !part)) {
    throw new Error("Unsupported broad or escaping release input path");
  }
  return path;
}

// Deliberately bounded to this repository's plain Docker patterns. A new pattern
// must be understood here before it can affect the image's freshness claim.
function glob(pattern) {
  if (/[\\\x00-\x1f\[\]?]/.test(pattern)) throw new Error("Unsupported .dockerignore pattern");
  let result = "";
  for (let index = 0; index < pattern.length; index++) {
    const char = pattern[index];
    if (char === "*" && pattern[index + 1] === "*") {
      index++;
      if (pattern[index + 1] === "/") { index++; result += "(?:.*/)?"; }
      else result += ".*";
    } else if (char === "*") result += "[^/]*";
    else result += char.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
  return new RegExp(`^${result}(?:/.*)?$`);
}

function ignoreRules(text) {
  return text.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith("#"))
    .map((line) => {
      const include = line.startsWith("!");
      const pattern = (include ? line.slice(1) : line).replace(/^\//, "").replace(/\/$/, "");
      if (!pattern || pattern === "." || pattern.split("/").includes("..")) {
        throw new Error("Unsupported .dockerignore pattern");
      }
      return { include, matches: glob(pattern) };
    });
}

function copySources(text, dockerfile) {
  const sources = [];
  for (const line of text.replace(/\\\r?\n/g, " ").split(/\r?\n/)) {
    if (/^\s*ADD\s/i.test(line)) throw new Error(`Unsupported ADD input in ${dockerfile}; use explicit COPY`);
    if (!/^\s*COPY\s/i.test(line)) continue;
    let value = line.trim().replace(/^COPY\s+/i, "");
    let fromStage = false;
    while (/^--(?:from|chown|chmod)=\S+\s/.test(value)) {
      fromStage ||= value.startsWith("--from=");
      value = value.replace(/^--\S+\s+/, "");
    }
    // Stage outputs are covered by their original context inputs and Dockerfile.
    if (fromStage) continue;
    if (value.startsWith("--") || /[\[\]'"$\\]/.test(value)) {
      throw new Error(`Unsupported COPY syntax in ${dockerfile}`);
    }
    const parts = value.trim().split(/\s+/);
    if (parts.length < 2) throw new Error(`Missing COPY inputs in ${dockerfile}`);
    for (const source of parts.slice(0, -1)) sources.push(relativePath(source));
  }
  if (!sources.length) throw new Error(`No context COPY inputs in ${dockerfile}`);
  return sources;
}

export async function sourceFingerprint(root = repoRoot) {
  const selectedRoot = resolve(root);
  const files = new Map();
  async function infoFor(path) {
    let info;
    let prefix = "";
    for (const part of path.split("/")) {
      prefix = prefix ? `${prefix}/${part}` : part;
      info = await lstat(join(selectedRoot, prefix)).catch((error) => {
        if (error.code === "ENOENT") throw new Error(`Missing release input: ${path}`);
        throw error;
      });
      if (info.isSymbolicLink()) throw new Error(`Unsupported release input symlink: ${prefix}`);
    }
    return info;
  }
  async function readControl(path) {
    if (!(await infoFor(path)).isFile()) throw new Error(`Invalid release control file: ${path}`);
    return readFile(join(selectedRoot, path), "utf8");
  }
  const ignoreText = await readControl(".dockerignore");
  const rules = ignoreRules(ignoreText);
  const ignored = (path) => {
    let excluded = false;
    for (const rule of rules) if (rule.matches.test(path)) excluded = !rule.include;
    return excluded;
  };
  async function collect(path, { required = false, control = false } = {}) {
    if (forbidden(path)) {
      if (required) throw new Error(`Forbidden release input: ${path}`);
      if (!ignored(path) && !ignored(`${path}/__release_probe__`)) {
        throw new Error(`Forbidden input is not excluded by .dockerignore: ${path}`);
      }
      return 0;
    }
    const info = await infoFor(path);
    if (info.isDirectory()) {
      let count = 0;
      for (const name of (await readdir(join(selectedRoot, path))).sort()) {
        count += await collect(relativePath(`${path}/${name}`));
      }
      if (required && !count) throw new Error(`Empty or excluded release input: ${path}`);
      return count;
    }
    if (!info.isFile()) throw new Error(`Unsupported release input type: ${path}`);
    if (!control && ignored(path)) {
      if (required) throw new Error(`Excluded release input: ${path}`);
      return 0;
    }
    files.set(path, digest(await readFile(join(selectedRoot, path))));
    return 1;
  }
  await collect(".dockerignore", { required: true, control: true });
  for (const dockerfile of dockerfiles) {
    await collect(dockerfile, { required: true, control: true });
    for (const source of copySources(await readControl(dockerfile), dockerfile)) {
      if (!source.includes("*")) { await collect(source, { required: true }); continue; }
      const slash = source.lastIndexOf("/");
      const directory = slash < 0 ? "" : source.slice(0, slash);
      const leaf = source.slice(slash + 1);
      if (directory.includes("*") || leaf.includes("**")) throw new Error("Unsupported COPY glob");
      if (forbidden(directory)) throw new Error("Forbidden COPY glob directory");
      if (directory && !(await infoFor(directory)).isDirectory()) throw new Error("Invalid COPY glob directory");
      const matches = (await readdir(join(selectedRoot, directory))).filter((name) => glob(leaf).test(name)).sort();
      if (!matches.length) throw new Error(`Missing release glob inputs: ${source}`);
      let count = 0;
      for (const name of matches) count += await collect(relativePath(directory ? `${directory}/${name}` : name));
      if (!count) throw new Error(`Excluded release glob inputs: ${source}`);
    }
  }
  const sorted = Object.fromEntries([...files].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0));
  const hash = createHash("sha256");
  for (const [path, sha256] of Object.entries(sorted)) hash.update(`${path}\0${sha256}\n`);
  return { sha256: hash.digest("hex"), files: sorted };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = process.argv.slice(2);
    if (args.some(arg=>!["--check","--objects-only"].includes(arg)) || new Set(args).size!==args.length) throw new Error("Usage: release-fingerprint.mjs [--check] [--objects-only]");
    const current = await sourceFingerprint();
    if (args.includes("--check")) {
      const evidence = JSON.parse(await readFile(join(repoRoot, args.includes("--objects-only")?"infra/release-object-evidence.json":"infra/release-evidence.json"), "utf8"));
      const recordedFiles = evidence.source?.files;
      if (evidence.schemaVersion !== 1 || evidence.source?.sha256 !== current.sha256 ||
          !recordedFiles || typeof recordedFiles !== "object" || Array.isArray(recordedFiles) ||
          Object.keys(recordedFiles).length !== Object.keys(current.files).length ||
          Object.entries(current.files).some(([path, hash]) => recordedFiles[path] !== hash)) {
        throw new Error("Release source evidence is missing or stale; rerun release verification");
      }
    }
    console.log(`Release source ${current.sha256} (${Object.keys(current.files).length} files)${args.includes("--check") ? " verified" : ""}`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

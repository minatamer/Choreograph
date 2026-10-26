// Isolated Linux acceptance: owned ephemeral resources, no host ports or providers.
import {spawnSync} from 'node:child_process';
import {randomBytes, randomUUID} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {sourceFingerprint} from './release-fingerprint.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const owner = `choreograph-release-${randomUUID()}`;
const label = `com.choreograph.release-smoke=${owner}`;
const pgImage = 'pgvector/pgvector:0.8.5-pg17-bookworm@sha256:d2ef61f42ef767baa5a1475393303cc235bcd92febd9d7014eddb48b41f3bad0';
const tags = {frontend: `choreograph-frontend:${owner}`, backend: `choreograph-api:${owner}`};
const images = {};
const env = {...process.env,
  POSTGRES_DB: 'choreograph_release', POSTGRES_USER: 'choreograph', POSTGRES_PASSWORD: randomBytes(24).toString('hex'),
  DATABASE_ENABLED: 'true', FAKE_MODE: 'true', PAID_DEMO_ENABLED: 'false', CHOREOGRAPH_ORIGIN: 'http://frontend:8080',
  CHOREOGRAPH_BRIDGE_SECRET: randomBytes(32).toString('hex'), CHOREOGRAPH_TOKEN_KEY: randomBytes(32).toString('base64url') + '=',
  CHOREOGRAPH_API_URL: 'http://api:8080', CHOREOGRAPH_API_AUTH: 'none',
  CHOREOGRAPH_TASK_URL: 'https://worker.example.invalid/internal/tasks/crm',
  CHOREOGRAPH_TASK_AUDIENCE: 'https://worker.example.invalid',
  CHOREOGRAPH_TASK_SERVICE_EMAIL: 'release-task@test-project.iam.gserviceaccount.com',
};
env.CHOREOGRAPH_DATABASE_URL = `postgresql+psycopg://choreograph:${env.POSTGRES_PASSWORD}@postgres:5432/choreograph_release`;
const backendNames = ['DATABASE_ENABLED','CHOREOGRAPH_DATABASE_URL','CHOREOGRAPH_ORIGIN','CHOREOGRAPH_BRIDGE_SECRET','CHOREOGRAPH_TOKEN_KEY','FAKE_MODE','PAID_DEMO_ENABLED'];
const frontendNames = ['CHOREOGRAPH_ORIGIN','CHOREOGRAPH_BRIDGE_SECRET','CHOREOGRAPH_API_URL','CHOREOGRAPH_API_AUTH'];
const ids = [];
let network, stage = 'fingerprint';
const checks = {};
const objectsOnly=process.argv.includes('--objects-only');
function docker(args, {input, timeout = 120000, allowFailure = false} = {}) {
  const r = spawnSync('docker', args, {cwd: root, env, windowsHide: true, encoding: 'utf8', input, timeout, maxBuffer: 8 * 1024 * 1024});
  if (r.error || r.status !== 0) {
    if (allowFailure) return null;
    throw new Error('DOCKER_COMMAND_FAILED');
  }
  return r.stdout.trim();
}
function envArgs(names) { return names.flatMap(name => ['--env', name]); }
function create(name, image, args = [], options = []) {
  const id = docker(['create','--name',`${owner}-${name}`,'--label',label,'--network',network,...options,image,...args]);
  if (!/^[a-f0-9]{64}$/.test(id)) throw new Error('RESOURCE_ID_INVALID');
  ids.push(id);
  return id;
}
function job(name, role, args = []) {
  const id = create(name,images.backend.id,['python','-m','choreograph.release',role,...args],
    ['--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=128m',...envArgs(backendNames)]);
  docker(['start','--attach',id]);
  if (docker(['inspect','--format','{{.State.ExitCode}}',id]) !== '0') throw new Error('RELEASE_JOB_FAILED');
}
async function ready(id, args) {
  for(let n = 0; n < 60; n++) {
    if (docker(['exec',id,...args], {allowFailure: true, timeout: 5000}) !== null) return;
    if (docker(['inspect','--format','{{.State.Running}}',id]) !== 'true') throw new Error('SERVICE_EXITED');
    await new Promise(resolve => setTimeout(resolve,500));
  }
  throw new Error('READINESS_TIMEOUT');
}
function owned(kind, id) {
  return docker([kind,'inspect','--format','{{index .Labels "com.choreograph.release-smoke"}}',id],{allowFailure:true}) === owner;
}
let evidence, failure;
try {
  const source = await sourceFingerprint(root);
  // Build exactly the source fingerprint being accepted; cache hits are fine.
  for (const [name, tag] of Object.entries(tags)) {
    stage = `build-${name}`;
    docker(['build','--platform','linux/amd64','--file',`infra/Dockerfile.${name}`,'--tag',tag,'.'],{timeout:900000});
    const r = JSON.parse(docker(['image','inspect','--format','{{json .}}',tag]));
    if(r.Os!=='linux'||r.Architecture!=='amd64'||!r.Config.User||['root','0','0:0'].includes(r.Config.User))throw new Error('RUNTIME_IDENTITY_INVALID');
    images[name] = {tag,id:r.Id,os:r.Os,architecture:r.Architecture,user:r.Config.User};
    console.log(JSON.stringify({stage,passed:true}));
  }
  stage = 'create-network';
  network = docker(['network','create','--internal','--label',label,owner]);
  if(!objectsOnly){
  stage = 'postgres';
  const pg = create('postgres',pgImage,[],['--network-alias','postgres','--tmpfs','/var/lib/postgresql/data:rw,noexec,nosuid,size=512m',...envArgs(['POSTGRES_DB','POSTGRES_USER','POSTGRES_PASSWORD'])]);
  docker(['start',pg]);
  await ready(pg,['pg_isready','--username','choreograph','--dbname','choreograph_release']);
  stage = 'schema-roundtrip';
  job('migrate','migrate');
  job('downgrade','schema-downgrade',['--target','base']);
  job('remigrate','migrate');
  checks.emptySchemaRoundtrip = true;
  stage = 'prepare-knowledge';
  job('prepare-knowledge','prepare-knowledge');
  checks.explicitFakeKnowledgePreparation = true;
  stage = 'readiness';
  job('readiness','readiness');
  checks.schemaProfileCorpusReadiness = true;
  stage = 'bootstrap';
  const bootstrap = create('bootstrap',images.backend.id,['python','-m','choreograph.release','bootstrap'],['--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=128m']);
  docker(['start',bootstrap]);
  await ready(bootstrap,['python','-c',"import json;from urllib.request import urlopen;assert json.load(urlopen('http://127.0.0.1:8080/health',timeout=2))=={'status':'bootstrap','application_ready':False}"]);
  checks.healthOnlyBootstrapWithoutSecrets = true;
  stage = 'api';
  const api = create('api',images.backend.id,[],['--network-alias','api','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=128m',...envArgs(backendNames)]);
  docker(['start',api]);
  await ready(api,['python','-c',"from urllib.request import urlopen; assert urlopen('http://127.0.0.1:8080/health',timeout=2).status == 200"]);
  stage = 'frontend';
  const frontend = create('frontend',images.frontend.id,[],['--network-alias','frontend','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=128m',...envArgs(frontendNames)]);
  docker(['start',frontend]);
  await ready(frontend,['node','-e',"fetch('http://127.0.0.1:8080/healthz').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]);
  stage = 'http-smoke';
  checks.http = JSON.parse(docker(['exec','--interactive',frontend,'node','--input-type=module'],{input:readFileSync(path.join(root,'scripts/release-http-smoke.mjs'),'utf8'),timeout:180000}));
  stage = 'skip-outbox';
  docker(['exec',api,'python','-c',"from sqlalchemy import text; from choreograph.db import build_engine; from choreograph.settings import load_environment; e=build_engine(load_environment()); c=e.connect(); assert c.execute(text('select count(*) from outbox')).scalar_one() == 0; c.close(); e.dispose()"]);
  checks.skippedCRMHasNoOutbox = true;
  stage = 'worker';
  const worker = create('worker',images.backend.id,['python','-m','choreograph.release','worker'],['--network-alias','worker','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=128m',...envArgs([...backendNames,'CHOREOGRAPH_TASK_URL','CHOREOGRAPH_TASK_AUDIENCE','CHOREOGRAPH_TASK_SERVICE_EMAIL'])]);
  docker(['start',worker]);
  await ready(worker,['python','-c',"from urllib.request import urlopen; assert urlopen('http://127.0.0.1:8080/health',timeout=2).status == 200"]);
  docker(['exec',frontend,'node','--input-type=module','-e',"const r=await fetch('http://worker:8080/internal/tasks/crm',{method:'POST',headers:{'content-type':'application/json'},body:'{}'});if(r.status!==403)process.exit(1);const g=await fetch('http://worker:8080/v1/session');if(g.status!==404)process.exit(1)"]);
  checks.privateWorkerRejectsUnauthenticated = true;
  stage = 'maintenance';
  job('maintenance','maintenance');
  checks.oneShotMaintenance = true;
  }
  if(objectsOnly){
    stage='object-frontend-http';
    const frontend=create('frontend',images.frontend.id,[],['--network-alias','frontend','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=128m',...envArgs(frontendNames)]);
    docker(['start',frontend]);
    await ready(frontend,['node','-e',"fetch('http://127.0.0.1:8080/healthz').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]);
    checks.frontendHTTP=JSON.parse(docker(['exec',frontend,'node','--input-type=module','-e',
      "const paths=['/healthz','/','/demo','/demo/workspace','/vendor/pdfjs/pdf.worker.min.mjs','/fonts/OFL.txt'];for(const path of paths){const r=await fetch('http://127.0.0.1:8080'+path);if(r.status!==200||r.headers.get('x-content-type-options')!=='nosniff'||r.headers.get('x-frame-options')!=='DENY')throw Error('FRONTEND_HTTP_FAILED');await r.arrayBuffer();}console.log(JSON.stringify({requests:paths.length,productionPagesAndAssets:true,securityHeaders:true}));"]));
  }
  stage = 'object-storage-process-smoke';
  const objectCheck = create('object-smoke',images.backend.id,['python','-'],
    ['--interactive','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=128m']);
  checks.objectStorage = JSON.parse(docker(['start','--attach','--interactive',objectCheck],
    {input:readFileSync(path.join(root,'scripts/object-linux-smoke.py'),'utf8'),timeout:180000}));
  if(checks.objectStorage.sql_connections!==0||checks.objectStorage.real_provider_calls!==0)throw new Error('OBJECT_SMOKE_ISOLATION_FAILED');
  stage = 'image-inspection';
  for (const image of Object.values(images))docker(['image','inspect','--format','{{.Id}}',image.id]);
  checks.nonRootLinuxImages = true;
  stage = 'freshness';
  if ((await sourceFingerprint(root)).sha256 !== source.sha256) throw new Error('SOURCE_CHANGED_DURING_ACCEPTANCE');
  evidence = {schemaVersion:1,verifiedAt:new Date().toISOString(),profile:objectsOnly?'local-isolated-linux-objects-fake':'local-isolated-linux-fake',source,images,checks,
    limitations:['No hosted CI run, deployment, Cloud SQL, Cloud Tasks delivery, IAM, live provider or owner acceptance verified.',objectsOnly?'Objects-only smoke excludes SQL and does not validate hosted GCS/IAM/queue behavior.':'Empty disposable schema roundtrip does not establish safety for downgrading populated data.']};
} catch (error) {
  failure = {stage,code:error.message};
} finally {
  const cleanupFailures = [];
  // Also recover a daemon-created resource whose create response was lost.
  const discovered = docker(['ps','--all','--quiet','--no-trunc','--filter',`label=${label}`],{allowFailure:true});
  if(discovered === null)cleanupFailures.push('container-discovery');
  const ownIDs = new Set([...ids,...(discovered?.split(/\s+/).filter(Boolean)??[])]);
  for (const id of [...ownIDs].reverse()) {
    // Container labels live under Config, unlike a network's top-level labels.
    const verified = docker(['inspect','--format','{{index .Config.Labels "com.choreograph.release-smoke"}}',id],{allowFailure:true}) === owner;
    if (!verified || docker(['rm','--force','--volumes',id],{allowFailure:true}) === null) cleanupFailures.push('container');
  }
  const discoveredNetworks = docker(['network','ls','--quiet','--no-trunc','--filter',`label=${label}`],{allowFailure:true});
  if(discoveredNetworks === null)cleanupFailures.push('network-discovery');
  const ownNetworks = new Set([...(network?[network]:[]),...(discoveredNetworks?.split(/\s+/).filter(Boolean)??[])]);
  for(const id of ownNetworks)if(!owned('network',id)||docker(['network','rm',id],{allowFailure:true})===null)cleanupFailures.push('network');
  if (cleanupFailures.length) failure = {stage:'cleanup',code:'OWNED_RESOURCE_CLEANUP_INCOMPLETE',prior:failure};
  if (evidence && !failure) evidence.checks.ownedResourcesRemoved = true;
}
if(failure){console.error(JSON.stringify({passed:false,...failure}));process.exitCode=1;}
else {
  if(!process.argv.includes('--no-receipt'))writeFileSync(path.join(root,objectsOnly?'infra/release-object-evidence.json':'infra/release-evidence.json'),JSON.stringify(evidence,null,2)+'\n');
  console.log(JSON.stringify({passed:true,profile:evidence.profile,sourceSha256:evidence.source.sha256,checks:evidence.checks,images:evidence.images}));
}

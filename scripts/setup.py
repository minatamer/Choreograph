"""Create only this checkout's local, fake-provider configuration. Never print secrets."""
import base64
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / ".env.local"
    if target.exists():
        print("Existing repo-local configuration preserved.")
        return
    password = secrets.token_hex(24)
    values = {
        "CHOREOGRAPH_PROFILE": "fake",
        "CHOREOGRAPH_DB_PASSWORD": password,
        "CHOREOGRAPH_DATABASE_URL": f"postgresql+psycopg://choreograph:{password}@127.0.0.1:45862/choreograph",
        "CHOREOGRAPH_ORIGIN": "http://127.0.0.1:45860",
        "CHOREOGRAPH_BRIDGE_SECRET": secrets.token_hex(32),
        "CHOREOGRAPH_TOKEN_KEY": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
    }
    with target.open("x", encoding="utf-8") as stream:
        stream.write("".join(f"{key}={value}\n" for key, value in values.items()))
    print("Repo-local fake configuration created; secrets omitted.")


if __name__ == "__main__":
    main()

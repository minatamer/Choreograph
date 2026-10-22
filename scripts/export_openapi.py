"""Export schemas without loading local secrets, database or provider clients."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/backend'))
from choreograph.api import create_app  # noqa: E402 - standalone export resolves the checkout source path first.
from choreograph.settings import Settings  # noqa: E402 - standalone export resolves the checkout source path first.

settings = Settings('postgresql+psycopg://unused:unused@127.0.0.1/choreograph_test_schema',
                    'http://127.0.0.1:45860', 'x'*40, 'x'*44, testing=True)
target = ROOT / 'apps/frontend/lib/generated/openapi.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(create_app(settings).openapi(), indent=2) + '\n', encoding='utf-8')
print('Public OpenAPI exported without runtime configuration.')

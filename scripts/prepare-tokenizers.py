"""Explicit public-asset preparation; never imported by an application entrypoint."""
import hashlib
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps' / 'backend'))
from choreograph.tokenizers import (  # noqa: E402 - explicit script entrypoint resolves this checkout only.
    ASSET_DIRECTORY,
    ASSETS,
    MAX_ASSET_BYTES,
    TOKENIZER_VERSION,
    verified_bytes,
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('TOKENIZER_DOWNLOAD_REDIRECT')


def main():
    ASSET_DIRECTORY.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    manifest = []
    for name, metadata in ASSETS.items():
        try:
            data = verified_bytes(name)
        except ValueError:
            # The only permitted network path is this explicit finite command.
            with opener.open(metadata['url'], timeout=30) as response:
                if response.status != 200:
                    raise ValueError('TOKENIZER_DOWNLOAD_FAILED') from None
                data = response.read(MAX_ASSET_BYTES + 1)
            if len(data) > MAX_ASSET_BYTES or hashlib.sha256(data).hexdigest() != metadata['sha256']:
                raise ValueError('TOKENIZER_DOWNLOAD_HASH_MISMATCH') from None
            target = ASSET_DIRECTORY / (name + '.tiktoken')
            with tempfile.NamedTemporaryFile(dir=ASSET_DIRECTORY, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
            try:
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        manifest.append({'name': name, 'file': name + '.tiktoken', 'url': metadata['url'],
                         'sha256': metadata['sha256'], 'bytes': len(data)})
    (ASSET_DIRECTORY / 'manifest.json').write_text(json.dumps({
        'source': 'https://github.com/openai/tiktoken/blob/0.14.0/tiktoken_ext/openai_public.py',
        'tiktoken_version': TOKENIZER_VERSION, 'license': 'MIT (LICENSE.tiktoken)',
        'preparation': 'Explicit scripts/prepare-tokenizers.py; application runtime reads local assets only.',
        'assets': manifest,
    }, indent=2) + '\n', encoding='utf-8')
    print('{"code":"TOKENIZER_ASSETS_VERIFIED","count":2}')


if __name__ == '__main__':
    main()

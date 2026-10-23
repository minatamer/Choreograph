"""Render original fictional source previews; never use these for guest replacements."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'assets/knowledge'
PUBLIC = ROOT / 'apps/frontend/public/guide-previews'
CATALOG = ROOT / 'apps/frontend/lib/sample-guides.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', help='Absolute path to pdftoppm')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest = [row for row in json.loads((PACK / 'manifest.json').read_text()) if not row['replacement']]
    if args.check:
        catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
        assert len(catalog) == len(manifest) == 6
        for source, preview in zip(manifest, catalog, strict=True):
            assert source['slot'] == preview['slot'] and digest(PACK / source['file']) == preview['sha256'] == source['sha256']
            assert source['pages'] == preview['pages']
            for page in preview['previews']:
                asset = PUBLIC / page['file']
                assert digest(asset) == page['sha256']
                with Image.open(asset) as image:
                    assert image.size == (page['width'], page['height'])
            if source['file'].endswith('.md'):
                assert preview['text'] == (PACK / source['file']).read_text(encoding='utf-8')
        print('Six original guide previews match canonical sources and rendered asset hashes.')
        return
    if not args.renderer:
        parser.error('--renderer is required to render PDFs')
    PUBLIC.mkdir(parents=True, exist_ok=True)
    temporary = ROOT / '.runtime/guide-previews'
    temporary.mkdir(parents=True, exist_ok=True)
    catalog = []
    for source in manifest:
        path = PACK / source['file']
        assert digest(path) == source['sha256']
        row = {key: source[key] for key in ('slot', 'title', 'version', 'file', 'pages', 'sha256')}
        row['previews'] = []
        if path.suffix == '.pdf':
            prefix = temporary / source['slot']
            subprocess.run([args.renderer, '-scale-to-x', '800', '-scale-to-y', '-1', '-png', str(path), str(prefix)], check=True, capture_output=True)
            for page in range(1, source['pages'] + 1):
                raster = temporary / f'{source["slot"]}-{page}.png'
                output = PUBLIC / f'{source["slot"]}-{page}.webp'
                with Image.open(raster) as image:
                    image.convert('RGB').save(output, 'WEBP', quality=86, method=6)
                    width, height = image.size
                row['previews'].append({'file': output.name, 'width': width, 'height': height, 'sha256': digest(output)})
                raster.unlink()
        else:
            row['text'] = path.read_text(encoding='utf-8')
        catalog.append(row)
    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Rendered original sample pages and the six-source preview catalog.')


if __name__ == '__main__':
    main()

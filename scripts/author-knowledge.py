"""Regenerate the original, labelled Juniper PDF assets from editable source."""
import argparse
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'assets' / 'knowledge'
BLUE = colors.HexColor('#1967D2')
STYLES = {
    'label': ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=10, textColor=BLUE, spaceAfter=17),
    'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=28, leading=33, spaceAfter=12, textColor=colors.HexColor('#202124')),
    'intro': ParagraphStyle('intro', fontSize=10, leading=15, textColor=colors.HexColor('#5F6368'), spaceAfter=26),
    'section': ParagraphStyle('section', fontName='Helvetica-Bold', fontSize=13, leading=18, spaceBefore=14, spaceAfter=7),
    'body': ParagraphStyle('body', fontSize=11, leading=17, spaceAfter=12),
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--slots',nargs='+',choices=['service','preparation','access','changes','safety'])
    args=parser.parse_args()
    guides = json.loads((PACK/'sources'/'guides.json').read_text(encoding='utf-8'))
    previous={item['file']:item for item in json.loads((PACK/'manifest.json').read_text(encoding='utf-8'))} if args.slots else {}
    manifest = []
    for guide in guides:
        if args.slots and guide['slot'] not in args.slots:
            manifest.append(previous[guide['file']])
            continue
        target = PACK / guide['file']
        doc = SimpleDocTemplate(str(target), pagesize=(595.28, 841.89), leftMargin=54, rightMargin=54,
                                topMargin=46, bottomMargin=55, title=guide['title'], author='Juniper Cleaning - fictional demo company')
        story = []
        for number, page in enumerate(guide['pages'], 1):
            if number > 1:
                story.append(PageBreak())
            story.extend([Paragraph('JUNIPER / CLEANING', STYLES['label']),
                          Paragraph(escape(guide['title']), STYLES['title']),
                          Paragraph(f"Fictional demo company | Version {guide['version']}<br/>Effective {guide.get('effective','22 October 2026')}", STYLES['intro']),
                          Paragraph(escape(page['heading']), STYLES['section']), Spacer(1, 4)])
            for heading, body in page['sections']:
                story.extend([Paragraph(escape(heading), STYLES['section']), Paragraph(escape(body), STYLES['body'])])
        def footer(canvas, document, guide=guide):
            canvas.setStrokeColor(colors.HexColor('#DADCE0')); canvas.line(54, 43, 541, 43)
            canvas.setFillColor(colors.HexColor('#5F6368')); canvas.setFont('Helvetica', 9)
            canvas.drawString(54, 28, 'Fictional guidance for the Choreograph demo')
            canvas.drawRightString(541, 28, f"v{guide['version']} / Page {document.page}")
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        manifest.append({k:guide[k] for k in ('slot','title','version','file')} | {
            'pages':len(guide['pages']), 'replacement':guide.get('replacement',False),
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    faq = PACK/'service-questions.md'
    faq_version=next(line.split()[1] for line in faq.read_text(encoding='utf-8').splitlines() if line.startswith('Version '))
    manifest.append({'slot':'questions','title':'Service Questions','version':faq_version,'file':faq.name,
                     'pages':1,'replacement':False,'sha256':hashlib.sha256(faq.read_bytes()).hexdigest()})
    (PACK/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Authored {sum(not args.slots or guide["slot"] in args.slots for guide in guides)} original PDFs and updated the FAQ manifest.')


if __name__=='__main__':
    main()

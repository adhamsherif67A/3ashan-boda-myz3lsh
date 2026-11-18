"""Package unaltered real photographs as a printable, location-free pilot brief."""
from pathlib import Path
import html
import json
import re
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4

HERE = Path(__file__).resolve().parent
OUT = HERE / 'briefing'
SOURCES = json.loads((OUT / 'sources.json').read_text())['query']['pages']
PHOTO_INFO = [
    ('01_bell_real.jpg', "TARGET 1 — SHIP'S BELL", "Brass bell, flared skirt and crown loop.",
     '2011 10 19 Cap Polonio', 'Dr. Karl-Heinz Hochhaus'),
    ('02_anchor_real.jpg', 'TARGET 2 — ADMIRALTY ANCHOR', 'Iron anchor, two flukes, long shank and cross-stock.',
     'Admiralty anchor', 'Mark.murphy (English Wikipedia)'),
    ('03_propeller_real.jpg', 'TARGET 3 — FOUR-BLADE PROPELLER', 'Weathered bronze, four swept blades and a hollow central hub.',
     'Propeller from ship', 'National Maritime Museum in Gdansk'),
]


def wrap(text, width=100):
    import textwrap
    return textwrap.wrap(text, width=width, break_long_words=False)


pdf = canvas.Canvas(str(OUT / 'pilot_photo_briefing.pdf'), pagesize=A4)
pdf.setTitle('Operation MX — Ocean search and survey: real-photo briefing')
credits = ['# Real reference photographs', '',
           'The JPEG files are unaltered photographs of physical objects, not renders or AI images.',
           'Simulation STLs are simplified shape references at training scale; they are not scans or exact replicas.',
           'No engraving, museum backgrounds, plinths or measurement annotations are part of the targets.', '']
width, height = A4
for filename, title, description, match, fallback_author in PHOTO_INFO:
    record = next(p for p in SOURCES.values() if match in p['title'])
    info = record['imageinfo'][0]
    meta = info['extmetadata']
    # Explicit known author is used where older Commons pages lack Artist metadata.
    raw_artist = meta.get('Artist', {}).get('value', fallback_author)
    artist = html.unescape(re.sub('<[^>]+>', '', raw_artist)).strip()
    license_name = meta['LicenseShortName']['value']
    license_url = meta.get('LicenseUrl', {}).get('value', '')
    source = info['descriptionurl']
    pdf.setFillColor(HexColor('#0b2636')); pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(HexColor('#58c9e8')); pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(32, height-45, 'OPERATION MX | SEARCH & SURVEY')
    pdf.setFillColor(HexColor('#ffffff')); pdf.setFont('Helvetica-Bold', 17)
    pdf.drawString(32, height-80, title.replace('—', '-'))
    pdf.setFont('Helvetica', 10); pdf.drawString(32, height-103, description)
    image = ImageReader(str(OUT / filename)); iw, ih = image.getSize()
    scale = min((width-64)/iw, 475/ih)
    dw, dh = iw*scale, ih*scale
    pdf.drawImage(image, (width-dw)/2, 190+(475-dh)/2, width=dw, height=dh)
    pdf.setFont('Helvetica-Bold', 11)
    pdf.drawString(32, 166, 'Pilot objective')
    pdf.setFont('Helvetica', 10)
    for i, line in enumerate([
        'Find all three objects using the ZED or bottom camera. Photograph each find,',
        'record its estimated position and inspect it without touching the object or cave.',
        'These are real reference photos; simulated objects use simplified geometry.',
    ]):
        pdf.drawString(32, 147-i*14, line)
    pdf.setFont('Helvetica', 8)
    for i, line in enumerate(wrap(f'Photo: {artist}. License: {license_name}. Unaltered photograph.', 112)):
        pdf.drawString(32, 85-i*11, line)
    pdf.setFillColor(HexColor('#58c9e8'))
    pdf.drawString(32, 48, 'Open photograph source and full license')
    pdf.linkURL(source, (32, 45, 320, 59), relative=0)
    pdf.showPage()
    credits += [f'## {title.title()}', '', f'- File: `{filename}`', f'- Author: {artist}',
                f'- Source: [{record["title"]}]({source})', f'- License: {license_name} {license_url}'.rstrip(),
                '- Original photograph retained without cropping or retouching.', '']
pdf.save()
(OUT / 'PHOTO_CREDITS.md').write_text('\n'.join(credits), encoding='utf-8')
(OUT / 'README.md').write_text('''# Pilot handout — ocean search and survey

Open `pilot_photo_briefing.pdf`, or use the three original JPEG photographs.
Find the three matching objects using the ZED or bottom RGB camera. For each
find, capture an identification image and record the estimated position.
Inspect without colliding with the scenery or targets. Return to the start.

The photographs show physical objects. The simulation meshes reproduce their
recognizable forms at training scale, without lettering or background scenery.
There are three targets in total; no pickup or automatic scoring is enabled.
This handout deliberately contains no target coordinates or cave map.

See PHOTO_CREDITS.md for image authors, source links and reuse licenses.
''')
with zipfile.ZipFile(HERE / 'pilot_photo_briefing.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
    for p in sorted(OUT.iterdir()):
        if p.is_file():
            bundle.write(p, p.name)
print('Created real-photo PDF and pilot briefing ZIP')

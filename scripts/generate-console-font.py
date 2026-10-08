"""Bake pinned Noto glyph coverage on the host; no font engine on the PS5."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json

root=Path(__file__).resolve().parents[1]
source=root/'console/vendor/noto-sans-display'
pins=json.loads((source/'source.json').read_text())
for name,digest in pins['files'].items():
    assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest
output=root/'.local/console-build/final-ui-font'
output.mkdir(parents=True,exist_ok=True)
# Latin-1 plus typographic punctuation needed for the interface.
points=list(range(32,127))+list(range(160,256))+[0x152,0x153,0x2019,0x2013,0x2014,0x2022,0x2026]
coverage=bytearray();glyphs=[];fonts=[]
for size in (22,26,32,40,56,72,88):
    font=ImageFont.truetype(str(source/'NotoSansDisplay.ttf'),size)
    font.set_variation_by_axes([500,100])
    start=len(glyphs)
    for point in points:
        char=chr(point);box=font.getbbox(char,anchor='ls')
        width,height=box[2]-box[0],box[3]-box[1]
        bitmap=Image.new('L',(max(1,width),max(1,height)))
        ImageDraw.Draw(bitmap).text((-box[0],-box[1]),char,font=font,fill=255,anchor='ls')
        glyphs.append((point,len(coverage),width,height,box[0],box[1],round(font.getlength(char))))
        coverage.extend(bitmap.tobytes() if width and height else b'')
    fonts.append((size,start,len(points)))
header='/* Generated from pinned OFL-1.1 Noto Sans Display; retain OFL.txt. */\n'
header+='static const unsigned char font_coverage[]={\n'
header+='\n'.join(','.join(str(b) for b in coverage[n:n+64])+',' for n in range(0,len(coverage),64))+'\n};\n'
header+='static const FontGlyph font_glyphs[]={\n'+''.join('{'+','.join(map(str,g))+'},\n' for g in glyphs)+'};\n'
header+='static const FontSize font_sizes[]={'+','.join('{'+','.join(map(str,f))+'}' for f in fonts)+'};\n'
(output/'font.inc').write_text(header,encoding='ascii',newline='\n')
print(f'Baked {len(fonts)} sizes / {len(glyphs)} glyphs / {len(coverage)} coverage bytes; pinned font/license verified.')

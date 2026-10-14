"""Draw a new TrophySync title icon from primitives; no test/icon source reused."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json

root=Path(__file__).resolve().parents[1]
font_root=root/'console/vendor/noto-sans-display'
pins=json.loads((font_root/'source.json').read_text())
assert hashlib.sha256((font_root/'NotoSansDisplay.ttf').read_bytes()).hexdigest()==pins['files']['NotoSansDisplay.ttf']
# Supersample native vector primitives for smooth title artwork.
image=Image.new('RGB',(1024,1024),'#080e1b');draw=ImageDraw.Draw(image)
for y in range(1024):
    ratio=y/1023
    draw.line((0,y,1024,y),fill=(int(18-10*ratio),int(42-26*ratio),int(78-49*ratio)))
draw.rounded_rectangle((206,100,818,712),radius=155,fill='#1654b0',outline='#72afff',width=3)
# Original trophy/sync silhouette, shared with web/app/icon.svg.
scale=9;ox=224;oy=118
points=lambda values:[(ox+x*scale,oy+y*scale) for x,y in values]
white='#f4f8ff';weight=24
draw.line(points([(51,23),(48,16),(42,11),(34,9),(26,9),(19,12),(13,17)]),fill=white,width=weight,joint='curve')
draw.line(points([(13,9),(13,17),(21,17)]),fill=white,width=weight,joint='curve')
draw.line(points([(13,41),(16,48),(22,53),(30,55),(38,55),(45,52),(51,47)]),fill=white,width=weight,joint='curve')
draw.line(points([(43,47),(51,47),(51,55)]),fill=white,width=weight,joint='curve')
draw.polygon(points([(24,19),(40,19),(40,31),(37,38),(32,41),(27,38),(24,31)]),fill=white)
draw.line(points([(24,23),(19,23),(19,28),(21,33),(26,35)]),fill=white,width=20,joint='curve')
draw.line(points([(40,23),(45,23),(45,28),(43,33),(38,35)]),fill=white,width=20,joint='curve')
draw.line(points([(32,41),(32,48)]),fill=white,width=20)
draw.line(points([(25,48),(39,48)]),fill=white,width=20)
font=ImageFont.truetype(str(font_root/'NotoSansDisplay.ttf'),84);font.set_variation_by_axes([600,100])
draw.text((512,772),'TrophySync',font=font,fill=white,anchor='mt')
caption=ImageFont.truetype(str(font_root/'NotoSansDisplay.ttf'),26)
draw.text((512,887),'YOUR TROPHIES. YOUR PROGRESS.',font=caption,fill='#9ebfe7',anchor='mt')
target=root/'artifacts/console/final-ui/PPSA99889/sce_sys/icon0.png';target.parent.mkdir(parents=True,exist_ok=True)
image.resize((512,512),Image.Resampling.LANCZOS).save(target)
print('New native title icon generated: TrophySync branding, no TEST text.')

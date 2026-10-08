"""Draw a new TrophySync title icon from primitives; no test/icon source reused."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json

root=Path(__file__).resolve().parents[1]
font_root=root/'console/vendor/noto-sans-display'
pins=json.loads((font_root/'source.json').read_text())
assert hashlib.sha256((font_root/'NotoSansDisplay.ttf').read_bytes()).hexdigest()==pins['files']['NotoSansDisplay.ttf']
# Supersample native vector primitives for smooth title artwork.
image=Image.new('RGB',(1024,1024),'#101116');draw=ImageDraw.Draw(image)
draw.rounded_rectangle((210,145,814,730),radius=130,fill='#2c263c',outline='#494056',width=3)
gold='#dfc593';weight=18
draw.line([(360,270),(665,270),(665,410),(640,476),(584,524),(512,551),(440,524),(384,476),(360,410),(360,270)],fill=gold,width=weight,joint='curve')
draw.line([(360,317),(286,317),(286,393),(304,426),(346,449),(395,449)],fill=gold,width=weight,joint='curve')
draw.line([(665,317),(738,317),(738,393),(720,426),(678,449),(629,449)],fill=gold,width=weight,joint='curve')
draw.line([(512,551),(512,637)],fill=gold,width=weight)
draw.line([(426,639),(598,639)],fill=gold,width=weight)
font=ImageFont.truetype(str(font_root/'NotoSansDisplay.ttf'),84);font.set_variation_by_axes([600,100])
draw.text((512,793),'TrophySync',font=font,fill='#f3f2f7',anchor='mt')
target=root/'artifacts/console/final-ui/PPSA99889/sce_sys/icon0.png';target.parent.mkdir(parents=True,exist_ok=True)
image.resize((512,512),Image.Resampling.LANCZOS).save(target)
print('New native title icon generated: TrophySync branding, no TEST text.')

"""Render the site's original trophy/sync mark for the native PS5 title."""
from pathlib import Path
from PIL import Image,ImageDraw
from math import atan2, cos, sin, sqrt

root=Path(__file__).resolve().parents[1]
# Supersample the existing vector brand. No generated artwork or new dependency.
image=Image.new('RGB',(1024,1024),'#080e1b');draw=ImageDraw.Draw(image)
gradient=Image.new('RGB',image.size);gradient_draw=ImageDraw.Draw(gradient)
for y in range(1024):
    ratio=y/1023
    gradient_draw.line((0,y,1024,y),fill=(int(37-28*ratio),int(122-74*ratio),int(255-126*ratio)))
mask=Image.new('L',image.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,1023,1023),radius=282,fill=255)
image.paste(gradient,(0,0),mask)
# Original trophy/sync silhouette, shared with web/app/icon.svg.
scale=12.8;ox=102.4;oy=102.4
points=lambda values:[(ox+x*scale,oy+y*scale) for x,y in values]
white='#ffffff';weight=38
def arc(start,end,radius=22):
    # SVG small circular arc, sweep=0, as used by the site's original mark.
    dx,dy=(start[0]-end[0])/2,(start[1]-end[1])/2
    factor=sqrt((radius*radius-dx*dx-dy*dy)/(dx*dx+dy*dy))
    cx,cy=(start[0]+end[0])/2-factor*dy,(start[1]+end[1])/2+factor*dx
    first,last=atan2(start[1]-cy,start[0]-cx),atan2(end[1]-cy,end[0]-cx)
    return points([(cx+radius*cos(first+(last-first)*n/64),cy+radius*sin(first+(last-first)*n/64)) for n in range(65)])
def stroke(vertices,width):
    draw.line(vertices,fill=white,width=width,joint='curve')
    # Round joins/caps also fill subpixel seams between supersampled segments.
    for x,y in vertices:
        draw.ellipse((x-width/2,y-width/2,x+width/2,y+width/2),fill=white)
def bezier(start,control1,control2,end):
    return [tuple((1-t)**3*start[k]+3*(1-t)**2*t*control1[k]+3*(1-t)*t*t*control2[k]+t**3*end[k] for k in range(2)) for t in (n/32 for n in range(33))]
stroke(arc((51,23),(13,17)),weight)
draw.line(points([(13,9),(13,17),(21,17)]),fill=white,width=weight,joint='curve')
stroke(arc((13,41),(51,47)),weight)
draw.line(points([(43,47),(51,47),(51,55)]),fill=white,width=weight,joint='curve')
cup=[(24,19),(40,19)]+bezier((40,31),(40,37),(36,41),(32,41))+bezier((32,41),(28,41),(24,37),(24,31))
draw.polygon(points(cup),fill=white)
stroke(points([(24,23),(19,23)]+bezier((19,28),(19,33),(22,35),(26,35))),32)
stroke(points([(40,23),(45,23)]+bezier((45,28),(45,33),(42,35),(38,35))),32)
draw.line(points([(32,41),(32,48)]),fill=white,width=32)
draw.line(points([(25,48),(39,48)]),fill=white,width=32)
target=root/'artifacts/console/final-ui/PPSA99889/sce_sys/icon0.png';target.parent.mkdir(parents=True,exist_ok=True)
image.resize((512,512),Image.Resampling.LANCZOS).save(target)
print('Native title icon generated: the website trophy/sync mark, 512px RGB.')

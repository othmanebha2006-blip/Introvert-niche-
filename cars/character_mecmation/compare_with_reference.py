import sys; sys.path.insert(0, "/home/user/Introvert-niche-/cars/lib")
import os, cairo, numpy as np
from PIL import Image
from mecmation_img import *
M=Mecmation()
cases=[("0010","rest","rest",0),("0060","arms_out","grin",0),("0160","hands_up","grin",0),("0215","present_R","grin",0),("0310","wave_R","grin",0),("0604","rest","rest",1)]
tiles=[]
for fn,g,v,bl in cases:
    s=cairo.ImageSurface(cairo.FORMAT_ARGB32,1080,952); c=cairo.Context(s); c.set_source_rgb(217/255,217/255,217/255); c.paint()
    arms=gesture_arms(M,g,g,1.0)
    M.draw(c,dict(x=535.5,ground=928.4+6*0,s=0.635,arms=arms,viseme=v,open=0.6,blink=bl,lean=gesture_lean(g,g,1)))
    s.write_to_png("mine.png")
    a=Image.open("mine.png").convert("RGB").crop((190,0,890,952)); b=Image.open(os.path.join(os.environ.get("FRAMES","frames"), f"{fn}.png")).convert("RGB").crop((190,0,890,952))
    t=Image.new("RGB",(1400,952)); t.paste(b,(0,0)); t.paste(a,(700,0)); tiles.append(t.resize((700,476)))
g=Image.new("RGB",(1400,476*3))
for i,t in enumerate(tiles): g.paste(t,((i%2)*700,(i//2)*476))
g.save("cmp.png")

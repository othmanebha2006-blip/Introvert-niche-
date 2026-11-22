import os
FRAMES = os.environ.get('FRAMES', 'frames')  # all frames of animation_reference.mov as 0001.png, 0002.png ...
import numpy as np
from PIL import Image
S,OX,OY=0.635,206.6,4.5
base=Image.open(os.path.join(FRAMES, "0055.png")).convert("RGB")
bl=base.convert("L")
def fit(im):
    g=im.convert("L"); best=None
    for ang in np.arange(-3.5,3.6,0.25):
        for dx in range(-16,17,1):
            r=bl.rotate(ang, resample=Image.BILINEAR, center=(536,375), translate=(dx,0))
            e=np.abs(np.asarray(r,np.float32)[20:230,360:700]-np.asarray(g,np.float32)[20:230,360:700]).mean()
            if best is None or e<best[0]: best=(e,ang,dx)
    return best
sk=np.array(base)[300,470].astype(float); print("ref skin", sk, np.array(base)[250,620])
SK_PNG=np.array([254,209,164],float)
def extract(fn, box, name):
    im=Image.open(os.path.join(FRAMES, f"{fn}.png")).convert("RGB")
    e,ang,dx=fit(im); print(fn,name,"fit",round(e,2),ang,dx)
    # undo head motion: rotate back
    un=im.rotate(0, translate=(-dx,0)).rotate(-ang, resample=Image.BICUBIC, center=(536,375))
    x0,y0,x1,y1=box
    crop=np.asarray(un.crop(box)).astype(float)
    # up-scale to png pixels
    W=int(round((x1-x0)/S)); H=int(round((y1-y0)/S))
    crop=np.asarray(Image.fromarray(crop.astype(np.uint8)).resize((W,H),Image.LANCZOS)).astype(float)
    d=np.sqrt(((crop-sk)**2).sum(2))
    a=np.clip((d-18)/55,0,1)
    col=np.where(a[...,None]>0.01,(crop-(1-a[...,None])*sk)/np.maximum(a[...,None],0.01),0)
    col=np.clip(col,0,255)
    rgba=np.dstack([col,a*255]).astype(np.uint8)
    px=(x0-OX)/S; py=(y0-OY)/S
    Image.fromarray(rgba).save(f"/home/user/Introvert-niche-/cars/character_mecmation/sprites/{name}.png")
    return name,round(px,1),round(py,1)
MB=(465,288,607,352); EB=(478,222,598,282)
out=[]
out.append(extract("0055",MB,"mouth_rest"))
out.append(extract("0052",MB,"mouth_grin"))
out.append(extract("0049",MB,"mouth_open"))
out.append(extract("0034",MB,"mouth_teeth"))
out.append(extract("0040",MB,"mouth_o_small"))
out.append(extract("0058",MB,"mouth_o"))
out.append(extract("0082",EB,"eyes_happy"))
out.append(extract("0055",EB,"eyes_open"))
print(out)

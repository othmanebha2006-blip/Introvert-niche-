import numpy as np, sys
from PIL import Image, ImageFilter
from scipy import ndimage
def cut(path):
    im=np.asarray(Image.open(path).convert('RGB')).astype(float)
    mx=im.max(2); mn=im.min(2); sat=(mx-mn)
    bgish=(mn>150)&(sat<28)          # white or light-grey shadow
    lab,n=ndimage.label(bgish)
    border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bg=np.isin(lab,list(border))
    fg=~bg
    fg=ndimage.binary_opening(fg,iterations=1)
    fg=ndimage.binary_fill_holes(fg)
    return im.astype(np.uint8), fg
def comps(fg,minarea):
    lab,n=ndimage.label(ndimage.binary_dilation(fg,iterations=6))
    out=[]
    for i,sl in enumerate(ndimage.find_objects(lab)):
        if (sl[0].stop-sl[0].start)*(sl[1].stop-sl[1].start)<minarea: continue
        out.append(sl)
    return sorted(out,key=lambda s:(round(s[0].start/150),s[1].start)), lab
def save(im,fg,sl,name,lab=None,idx=None):
    m=fg[sl].copy()
    a=Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    rgba=Image.fromarray(im[sl]).convert('RGBA'); rgba.putalpha(a)
    rgba.save(name); print(name,rgba.size)
import os
os.makedirs('cut',exist_ok=True)
for path,prefix in [('84dcbcbb-image.png','gf_ref'),('0d189ee1-image.png','bf_ref'),('efdc538f-image.png','gf'),('cade9d91-image.png','bf')]:
    im,fg=cut(path); sls,lab=comps(fg,20000)
    for k,sl in enumerate(sls): save(im,fg,sl,f'cut/{prefix}_{k}.png')

# cut a note photographed on a plain warm background: the background is modelled per pixel (it can shade slightly),
# alpha comes from colour distance to it, and the background is taken back out of the soft edges, so what is left at an edge is warm and pale
import cv2, numpy as np, os, sys
from PIL import Image
src, slug, out = sys.argv[1], sys.argv[2], sys.argv[3]
a=np.asarray(Image.open(src).convert("RGB")).astype(np.float32)/255
lab=cv2.cvtColor(a,cv2.COLOR_RGB2LAB)
h,w=a.shape[:2]
border=np.concatenate([lab[:20].reshape(-1,3),lab[:, :20].reshape(-1,3),lab[:, -20:].reshape(-1,3)])
bg0=np.median(border,0)
d0=np.linalg.norm(lab-bg0,axis=2)
rough=(cv2.GaussianBlur(d0,(0,0),2)>12).astype(np.uint8)
rough=cv2.dilate(rough,np.ones((25,25),np.uint8))
# background model: fill the subject area from the surrounding background, smooth
sm=cv2.resize(a,(w//8,h//8),interpolation=cv2.INTER_AREA); rm=cv2.resize(rough,(w//8,h//8),interpolation=cv2.INTER_NEAREST)
bgs=cv2.inpaint((sm*255).astype(np.uint8),rm,15,cv2.INPAINT_TELEA).astype(np.float32)/255
bgs=cv2.GaussianBlur(bgs,(0,0),6); bg=cv2.resize(bgs,(w,h),interpolation=cv2.INTER_CUBIC)
blab=cv2.cvtColor(bg,cv2.COLOR_RGB2LAB)
d=np.linalg.norm(lab-blab,axis=2)
al=np.clip((d-6)/14,0,1)
core=(cv2.GaussianBlur(d,(0,0),2)>10).astype(np.uint8)
n,l,st,_=cv2.connectedComponentsWithStats(core,8); keep=np.zeros_like(core)
for i in range(1,n):
    if st[i,4]>3000: keep[l==i]=1
inv=(1-keep).astype(np.uint8); n2,l2,s2,_=cv2.connectedComponentsWithStats(inv,4)
for i in range(1,n2):
    x,y,ww,hh,ar=s2[i]
    if ar<800 and x>0 and y>0 and x+ww<w and y+hh<h: keep[l2==i]=1; al[l2==i]=np.maximum(al[l2==i],0.97)
al=al*cv2.dilate(keep,np.ones((7,7),np.uint8))
fg=np.clip((a-(1-al[...,None])*bg)/np.maximum(al[...,None],0.05),0,1)
fg=np.where(al[...,None]>0.02,fg,bg)
ys,xs=np.where(al>0.05); y0,y1,x0,x1=max(0,ys.min()-12),min(h,ys.max()+1),max(0,xs.min()-12),min(w,xs.max()+13)
im=Image.fromarray((np.dstack([fg,al])[y0:y1,x0:x1]*255).astype(np.uint8),"RGBA")
H=1100; im=im.resize((round(im.width*H/im.height),H),Image.LANCZOS)
os.makedirs(out,exist_ok=True); im.save(os.path.join(out,slug+".webp"),"WEBP",quality=90,alpha_quality=95,method=6)
A=np.asarray(im)[...,3].astype(np.float32)/255; L=np.asarray(im.convert("L")).astype(np.float32)/255
g=cv2.GaussianBlur(A,(0,0),25); dd=0.55*g/max(1e-3,g.max())+0.45*cv2.GaussianBlur(L*A,(0,0),8); dd=(dd-dd.min())/(dd.max()-dd.min())
Image.fromarray((dd*255).astype(np.uint8)).resize((im.width//2,im.height//2),Image.LANCZOS).save(os.path.join(out,slug+"-depth.webp"),"WEBP",quality=90)
print(slug, im.size, "bg", np.round(bg0,1), "bottom cover", round(float((np.asarray(im)[-3:,:,3]>128).mean()),3))

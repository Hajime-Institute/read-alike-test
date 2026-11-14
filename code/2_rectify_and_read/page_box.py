# -*- coding: utf-8 -*-
"""本物の撮影(90° 回した後)で、ページが写っている範囲を測る。赤い台の上の白い紙を、彩度の低さと明るさで切り出す。"""
import sys, cv2, numpy as np, json, os

def page_mask(im):
    """ページの画素。背景は赤い台なので「赤み(R-max(G,B))が小さい」画素をページとする。
    (最初は「彩度が低く明るい」で切っていたが、影のかかったページの下端が外れた)"""
    b,g,r=[im[...,i].astype(np.int16) for i in range(3)]
    return (((r-np.maximum(g,b))<35)&((r+g+b)>150)).astype(np.uint8)*255
def page_box(path, rot=90):
    im=cv2.imread(path)
    if rot==90: im=cv2.rotate(im,cv2.ROTATE_90_CLOCKWISE)
    m=page_mask(im)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    c=max(cs,key=cv2.contourArea); x,y,w,h=cv2.boundingRect(c)
    return dict(x=int(x),y=int(y),w=int(w),h=int(h),img_w=im.shape[1],img_h=im.shape[0])
if __name__=="__main__":
    out={os.path.basename(p):page_box(p) for p in sys.argv[2:]}
    json.dump(out,open(sys.argv[1],"w"),indent=1)
    for k,v in out.items(): print(k,v["w"],v["h"],"page ~%.0f dpi"%(v["w"]/8.27))

# -*- coding: utf-8 -*-
"""Blur generators used by the read-alike test experiments (defocus: uniform disk, depth-varying, tilted-page plane; motion).
Trimmed from the authors' internal degradation library to the functions the paper uses; the functions themselves are unchanged."""
import cv2, numpy as np
RNG=np.random.default_rng(20260616)
MOTION=[2,4,7,10,14,19,25]            # 手ぶれの長さ(px @200dpi)
DEFOCUS=[1.0,1.8,2.6,3.6,4.8,6.2,8.0] # ピンぼけの円の半径(px)

def f_motion(img,l,length=None,ang=None):
    """length(px)・ang(度、0=横)を渡すと段の代わりに使う(本物の撮影に合わせ込むとき)。"""
    k=int(length) if length is not None else MOTION[l]
    ang=float(ang) if ang is not None else float(RNG.uniform(0,180))
    ker=np.zeros((k*2+1,k*2+1),np.float32); c=k
    dx,dy=np.cos(np.deg2rad(ang)),np.sin(np.deg2rad(ang))
    cv2.line(ker,(int(c-dx*k),int(c-dy*k)),(int(c+dx*k),int(c+dy*k)),1.0,1)
    return cv2.filter2D(img,-1,ker/ker.sum(),borderType=cv2.BORDER_REPLICATE)

def _disk_kernel(r,ss=8):
    """半径 r(小数のまま)の円のぼけの核。8 倍の細かさで円を描いて面積で縮める(縁の画素は円が覆う割合の重み)。
    (2026-11-04 まで半径を整数に丸めていて、1.5 と 2.5、4.75 と 5.25 が同じ核になっていた)"""
    n=int(np.ceil(r))*2+3; big=np.zeros((n*ss,n*ss),np.float32); c=(n*ss-1)/2.0
    yy,xx=np.mgrid[0:n*ss,0:n*ss]; big[((xx-c)**2+(yy-c)**2)<=(r*ss)**2]=1.0
    ker=cv2.resize(big,(n,n),interpolation=cv2.INTER_AREA); return ker/ker.sum()

def f_defocus(img,l,radius=None):
    r=float(radius) if radius is not None else DEFOCUS[l]
    return cv2.filter2D(img,-1,_disk_kernel(r),borderType=cv2.BORDER_REPLICATE)

def _disk(img,r):
    if r<0.25: return img
    return cv2.filter2D(img,-1,_disk_kernel(r),borderType=cv2.BORDER_REPLICATE)

def f_defocus_var(img,r_center,r_edge,shape="radial",power=2.0):
    """場所で半径が変わるピンぼけ(2026-11-03)。本物のピンぼけ(SmartDoc-QA の Nokia Ob820)は、ページの中ほどは読め、
    上下の端で読めなくなっていた。一様なぼけは、ある半径で全体が一度に読めなくなる(崖)。
    shape: radial=中心から外へ(像面の湾曲) / vertical=上下の端へ(ページの傾き)。
    半径の地図 R=r_center+(r_edge-r_center)*d^power を作り、いくつかの半径でぼかした画像を画素ごとに補間する。"""
    h,w=img.shape[:2]; g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) if img.ndim==3 else img
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    if shape=="radial": d=np.sqrt(((xx-w/2)/(w/2))**2+((yy-h/2)/(h/2))**2)/np.sqrt(2)
    else: d=np.abs(yy-h/2)/(h/2)
    R=r_center+(r_edge-r_center)*np.clip(d,0,1)**power
    rs=np.unique(np.round(np.linspace(R.min(),R.max(),9),2))
    stack=np.stack([_disk(g,float(r)).astype(np.float32) for r in rs])
    if len(rs)==1: out=stack[0]
    else:
        idx=np.clip(np.searchsorted(rs,R)-1,0,len(rs)-2); r0=rs[idx]; r1=rs[idx+1]
        t=np.clip((R-r0)/np.maximum(r1-r0,1e-6),0,1)
        a=np.take_along_axis(stack,idx[None],0)[0]; b=np.take_along_axis(stack,(idx+1)[None],0)[0]
        out=a*(1-t)+b*t
    out=np.clip(out,0,255).astype(np.uint8)
    return cv2.cvtColor(out,cv2.COLOR_GRAY2BGR)

def _defocus_map(img,R,color=False):
    """半径の地図 R(画素ごと)でぼかす。いくつかの半径でぼかした画像を画素ごとに補間する(f_defocus_var と同じ作り)。
    color=True ならカラーのまま色ごとにぼかす(本物の撮影はカラー。色で刷られた見出しや段落の濃さが灰色にすると変わる)。"""
    if color and img.ndim==3:
        return np.dstack([_defocus_map(img[:,:,c],R)[:,:,0] for c in range(3)])
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) if img.ndim==3 else img
    rs=np.unique(np.round(np.linspace(R.min(),R.max(),9),2))
    stack=np.stack([_disk(g,float(r)).astype(np.float32) for r in rs])
    if len(rs)==1: out=stack[0]
    else:
        idx=np.clip(np.searchsorted(rs,R)-1,0,len(rs)-2); r0=rs[idx]; r1=rs[idx+1]
        t=np.clip((R-r0)/np.maximum(r1-r0,1e-6),0,1)
        a=np.take_along_axis(stack,idx[None],0)[0]; b=np.take_along_axis(stack,(idx+1)[None],0)[0]
        out=a*(1-t)+b*t
    return cv2.cvtColor(np.clip(out,0,255).astype(np.uint8),cv2.COLOR_GRAY2BGR)

def f_defocus_plane(img,r_top,r_bottom,r_tilt_x=0.0,color=False):
    """傾いた紙のピンぼけ(2026-11-05)。カメラに対して紙が少し傾くと、紙の上の深さは位置の一次式になり、
    ぼけの円の半径も(焦点の面からの距離にほぼ比例して)一次式で変わる。SmartDoc-QA の本物は上下の片側だけが
    強くぼけていて、中心から対称な f_defocus_var の vertical では表せなかった。
    R(x,y)=|r_top+(r_bottom-r_top)*y/h + r_tilt_x*(x/w-0.5)|。r_top を負にすると、焦点の面が紙を横切る(その行が一番鮮明)。"""
    h,w=img.shape[:2]; yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    R=np.abs(r_top+(r_bottom-r_top)*yy/(h-1)+r_tilt_x*(xx/(w-1)-0.5))
    return _defocus_map(img,R,color)

def f_motion_curve(img,length,curv=0.5,ang=0.0):
    """曲がった軌跡の手ぶれ(2 次元の手ぶれ。SmartDoc-QA の Mb2 に合わせる)。軌跡は 2 次ベジェ曲線で、
    curv は真ん中の制御点を長さの何割だけ横にずらすか。"""
    L=float(length); n=int(np.ceil(L*(1+abs(curv))))*2+3; ker=np.zeros((n,n),np.float32); c=n//2
    th=np.deg2rad(ang); ux,uy=np.cos(th),np.sin(th); px,py=-uy,ux
    p0=np.array([c-ux*L/2,c-uy*L/2]); p2=np.array([c+ux*L/2,c+uy*L/2]); p1=np.array([c+px*L*curv,c+py*L*curv])
    t=np.linspace(0,1,int(L*4)+8)[:,None]; pts=((1-t)**2*p0+2*(1-t)*t*p1+t**2*p2)
    pts-=pts.mean(0)-c                       # 軌跡の重心を真ん中に(像がずれないように)
    for x,y in pts:
        xi,yi=int(round(x)),int(round(y))
        if 0<=xi<n and 0<=yi<n: ker[yi,xi]+=1
    return cv2.filter2D(img,-1,ker/ker.sum(),borderType=cv2.BORDER_REPLICATE)

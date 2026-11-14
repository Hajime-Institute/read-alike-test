# -*- coding: utf-8 -*-
"""傾き(透視)の合成。本物の撮影(90° 回した後)からページの四隅を検出し、元の PDF をその四角形に貼り込む。
角度の数値から変換を組み立てるより、撮影 1 枚ごとの傾きを正確に写せる。背景は本物の背景の中央値の色で塗る。
使い方: python -I make_persp.py <出力先> <本物の画像...>   出力名: synP_<本物の名前>.jpg"""
import sys, os, re, subprocess, tempfile, cv2, numpy as np

def page_mask(im):
    """ページの画素。背景は赤い台なので「赤み(R-max(G,B))が小さい」画素をページとする。
    (最初は「彩度が低く明るい」で切っていたが、影のかかったページの下端が外れた)"""
    b,g,r=[im[...,i].astype(np.int16) for i in range(3)]
    return (((r-np.maximum(g,b))<35)&((r+g+b)>150)).astype(np.uint8)*255
HERE=os.path.dirname(os.path.abspath(__file__)); DATA=os.path.join(HERE,"..","data_smartdoc")
def quad(im):
    m=page_mask(im)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
    c=max(cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0],key=cv2.contourArea)
    peri=cv2.arcLength(c,True)
    for eps in (0.01,0.02,0.03,0.05):
        ap=cv2.approxPolyDP(c,eps*peri,True)
        if len(ap)==4: break
    else: ap=cv2.boxPoints(cv2.minAreaRect(c)).reshape(-1,1,2)
    p=ap.reshape(4,2).astype(np.float32); s=p.sum(1); d=np.diff(p,axis=1).ravel()
    return np.array([p[np.argmin(s)],p[np.argmin(d)],p[np.argmax(s)],p[np.argmax(d)]],np.float32), m   # 左上・右上・右下・左下
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
XDOC=os.environ.get("XDOC")=="1"   # 1 なら、四隅を同じ機種・同じ角度の「次の文書」の撮影から取る(確かめる撮影の四隅を使わない)
for path in sys.argv[2:]:
    name=os.path.basename(path); doc=re.search(r"_D(\d+)_",name).group(1)
    im=cv2.rotate(cv2.imread(path),cv2.ROTATE_90_CLOCKWISE)
    if XDOC:
        src=path.replace(f"_D{doc}_",f"_D{int(doc)%10+1}_")
        q,_=quad(cv2.rotate(cv2.imread(src),cv2.ROTATE_90_CLOCKWISE)); _,mask=quad(im)
    else: q,mask=quad(im)
    wpx=float(np.linalg.norm(q[1]-q[0])+np.linalg.norm(q[2]-q[3]))/2; dpi=int(round(wpx/8.27*1.1))   # 少し大きく描いて縮める
    tmp=tempfile.mkdtemp(); subprocess.run(["pdftoppm","-r",str(dpi),"-gray","-png","-singlefile",os.path.join(DATA,"Original_documents",f"page_{doc}.pdf"),tmp+"/p"],check=True,capture_output=True)
    pg=cv2.cvtColor(cv2.imread(tmp+"/p.png",cv2.IMREAD_GRAYSCALE),cv2.COLOR_GRAY2BGR); h,w=pg.shape[:2]
    H=cv2.getPerspectiveTransform(np.float32([[0,0],[w,0],[w,h],[0,h]]),q)
    bg=np.median(im[mask==0].reshape(-1,3),axis=0) if (mask==0).any() else np.array([128,128,128])
    canvas=np.empty_like(im); canvas[:]=bg.astype(np.uint8)
    warped=cv2.warpPerspective(pg,H,(im.shape[1],im.shape[0]),flags=cv2.INTER_AREA,borderMode=cv2.BORDER_TRANSPARENT,dst=canvas)
    ok,enc=cv2.imencode(".jpg",canvas,[int(cv2.IMWRITE_JPEG_QUALITY),90]); open(os.path.join(out,("synX_" if XDOC else "synP_")+name),"wb").write(enc.tobytes())
    print(name, "quad", q.astype(int).tolist(), "dpi", dpi, flush=True)

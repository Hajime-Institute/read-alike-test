# -*- coding: utf-8 -*-
"""本物の撮影(90° 回した後)のページの四隅を検出し、まっすぐな長方形(A4 の縦横比)に貼り直す。
docTR の既定はページがまっすぐだと仮定して行をまとめるので、わずかな傾きでも読む順が崩れた(きれいな撮影で 0.654)。
四隅の検出は make_persp.py の quad と同じ。使い方: python -I rectify_page.py <出力先> <画像...> → rect_<名前>.png"""
import sys, os, cv2, numpy as np, importlib.util
HERE=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(HERE,"make_persp.py")).read().split("out=sys.argv[1]")[0]   # quad と page_mask の定義だけを使う
ns={"__file__":os.path.join(HERE,"make_persp.py")}; exec(compile(src,"make_persp_defs","exec"),ns); quad=ns["quad"]
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for p in sys.argv[2:]:
    im=cv2.rotate(cv2.imread(p),cv2.ROTATE_90_CLOCKWISE); q,_=quad(im)
    w=int((np.linalg.norm(q[1]-q[0])+np.linalg.norm(q[2]-q[3]))/2); h=int(w*297/210)
    H=cv2.getPerspectiveTransform(q,np.float32([[0,0],[w,0],[w,h],[0,h]]))
    cv2.imwrite(os.path.join(out,"rect_"+os.path.basename(p).rsplit(".",1)[0]+".png"),cv2.warpPerspective(im,H,(w,h),flags=cv2.INTER_CUBIC))
    print("ok",os.path.basename(p),w,h,flush=True)

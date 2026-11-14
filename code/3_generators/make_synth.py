# -*- coding: utf-8 -*-
"""元の PDF を本物の撮影と同じ解像度で画像にし、degrade_lab の撮影の操作(f_motion・f_defocus)をかけて合成の相方を作る。
使い方: python -I make_synth.py <degrade_lab のパス> <出力先> <doc> <dpi> <phone> <kind> <値...>
kind: none / motion_v(縦の手ぶれ、長さ px。Mb1 の横の手ぶれは 90° 回した後のページでは縦になる) / defocus(半径 px) / defocusvar / defocusplane / motioncurve"""
import sys, os, subprocess, tempfile, cv2, numpy as np
lab,out,doc,dpi,phone,kind=sys.argv[1:7]; vals=sys.argv[7:]
sys.path.insert(0,lab); import degrade as D
pdf=os.path.join(os.path.dirname(out.rstrip("/")),"..","data_smartdoc","Original_documents",f"page_{doc}.pdf")
pdf=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","data_smartdoc","Original_documents",f"page_{doc}.pdf"))
COLOR=os.environ.get("COLOR")=="1"   # 1 ならカラーで描いてカラーのままぼかす(本物の撮影はカラー)
tmp=tempfile.mkdtemp(); subprocess.run(["pdftoppm","-r",dpi]+([] if COLOR else ["-gray"])+["-png","-singlefile",pdf,tmp+"/p"],check=True)
clean=cv2.imread(tmp+"/p.png") if COLOR else cv2.cvtColor(cv2.imread(tmp+"/p.png",cv2.IMREAD_GRAYSCALE),cv2.COLOR_GRAY2BGR)
os.makedirs(out,exist_ok=True)
for v in (vals or ["0"]):
    if os.environ.get("SKIP_EXISTING")=="1" and os.path.exists(os.path.join(out,f"syn_D{doc}_{phone}_{kind}{os.environ.get('KIND_SUFFIX','')}_{v}.jpg")): continue   # 作り済み(読みの記録がある)は作り直さない
    if kind=="none": im=clean
    elif kind=="motion_v": im=D.f_motion(clean,0,length=float(v),ang=90)
    elif kind=="defocus": im=D.f_defocus(clean,0,radius=float(v))
    elif kind=="defocusvar":           # v = 中央の半径:端の半径:形(radial/vertical)
        r0,r1,sh=v.split(":"); im=D.f_defocus_var(clean,float(r0),float(r1),sh)
    elif kind=="defocusplane":         # v = 上の半径:下の半径[:横の傾き](傾いた紙。半径は位置の一次式)
        p_=[float(x) for x in v.split(":")]; im=D.f_defocus_plane(clean,*p_,color=COLOR)
    elif kind=="motioncurve":          # v = 長さ:曲がり:向き(度)
        L_,c_,a_=v.split(":"); im=D.f_motion_curve(clean,float(L_),float(c_),float(a_))
    else: raise ValueError(kind)
    ok,enc=cv2.imencode(".jpg",im,[int(cv2.IMWRITE_JPEG_QUALITY),90])      # スマホの保存と同じく JPEG にする
    p=os.path.join(out,f"syn_D{doc}_{phone}_{kind}{os.environ.get('KIND_SUFFIX','')}_{v}.jpg"); open(p,"wb").write(enc.tobytes()); print(p)

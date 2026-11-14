# -*- coding: utf-8 -*-
"""よく使われる合成劣化(他人の作った生成器)で、ピンぼけの合成を作る。検査にかけるため。
albumentations 2.0.8: Defocus(一様な円のぼけ)・GaussianBlur(一様なガウス)。Augraphy 8.2.6: DepthSimulatedBlur(楕円の一部をぼかす)。
元の PDF を Nokia のページと同じ 208dpi で画像にし、各設定を乱数の種を固定してかけ、JPEG 90 で保存する。
使い方: .venv_aug/bin/python -I make_audit.py <出力先> <doc...>"""
import sys, os, subprocess, tempfile, random, numpy as np, cv2
import albumentations as A
from augraphy import DepthSimulatedBlur
HERE=os.path.dirname(os.path.abspath(__file__)); out=sys.argv[1]; os.makedirs(out,exist_ok=True)
# 機種と解像度(既定は Nokia の 208dpi)。Samsung は PHONE=Android DPI=285 で、ぼけが強いので半径とσの範囲を広げる
PHONE=os.environ.get("PHONE","WP"); DPI=os.environ.get("DPI","208")
RADII=(3,4,5,6,7,8) if PHONE=="WP" else (3,4,5,6,7,8,10,12,14)
SIGMAS=(1.0,1.5,2.0,2.5,3.0,3.5,4.0) if PHONE=="WP" else (1.0,1.5,2.0,2.5,3.0,3.5,4.0,5.0,6.0)
ELL=((120,200),(400,600),(800,1200)) if PHONE=="WP" else ((160,270),(550,820),(1100,1650))   # 楕円の大きさも解像度の比で広げる
if os.environ.get("GRID")=="dense":      # 候補を細かくする(傾いた紙のぼけ 120〜152 通りとの差を縮める)。既存の名前と重なる設定は作り済みとして飛ぶ
    RADII=tuple(x/2 for x in range(4,19)) if PHONE=="WP" else tuple(x/2 for x in range(4,31))          # 2〜9 / 2〜15 を 0.5 刻み
    SIGMAS=tuple(x/4 for x in range(3,19)) if PHONE=="WP" else tuple(x/4 for x in range(3,29))         # 0.75〜4.5 / 0.75〜7 を 0.25 刻み
    ELL=((80,140),(120,200),(250,400),(400,600),(800,1200)) if PHONE=="WP" else ((110,190),(160,270),(340,550),(550,820),(1100,1650))
def _r(x): return f"{x:g}" if isinstance(x,float) and x!=int(x) else str(int(x))
SETTINGS=[("albDefocus",f"{_r(r)}:{a}",lambda r=r,a=a: A.Defocus(radius=(r,r),alias_blur=(a,a),p=1.0)) for r in RADII for a in (0.1,0.5)]
SETTINGS+=[("albGauss",f"{s}",lambda s=s: A.GaussianBlur(blur_limit=0,sigma_limit=(s,s),p=1.0)) for s in SIGMAS]
SETTINGS+=[("augDepth",f"{lo}-{hi}:s{seed}",lambda lo=lo,hi=hi: DepthSimulatedBlur(blur_center="random",blur_major_axes_length_range=(lo,hi),
            blur_minor_axes_length_range=(lo,hi),blur_iteration_range=(8,10),p=1)) for lo,hi in ELL for seed in (0,1,2)]
ONLY=os.environ.get("AUDIT_ONLY","")      # alb / depth / 空=全部
DEPTH_KEEP=set(os.environ.get("DEPTH_KEEP","").split(",")) - {""}   # 例: 120-200:s0,400-600:s0(重いので数を絞る)
for doc in sys.argv[2:]:
    tmp=tempfile.mkdtemp(); subprocess.run(["pdftoppm","-r",DPI,"-gray","-png","-singlefile",
        os.path.join(HERE,"..","data_smartdoc","Original_documents",f"page_{doc}.pdf"),tmp+"/p"],check=True,capture_output=True)
    clean=cv2.cvtColor(cv2.imread(tmp+"/p.png",cv2.IMREAD_GRAYSCALE),cv2.COLOR_GRAY2BGR)
    for gen,param,mk in SETTINGS:
        if ONLY=="alb" and not gen.startswith("alb"): continue
        if ONLY=="depth" and not gen.startswith("aug"): continue
        if gen.startswith("aug") and DEPTH_KEEP and param not in DEPTH_KEEP: continue
        dst=os.path.join(out,f"syn_D{doc}_{PHONE}_{gen}_{param}.jpg")
        if os.path.exists(dst): continue          # 作り済みは飛ばす
        seed=int(param.split(":s")[1]) if ":s" in param else 0
        random.seed(seed); np.random.seed(seed)
        t=mk()
        im=t(image=clean)["image"] if gen.startswith("alb") else t(clean)
        ok,enc=cv2.imencode(".jpg",im,[int(cv2.IMWRITE_JPEG_QUALITY),90])
        open(dst,"wb").write(enc.tobytes())
    print("doc",doc,"done",len(SETTINGS),flush=True)

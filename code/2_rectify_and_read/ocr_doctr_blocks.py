# -*- coding: utf-8 -*-
"""docTR を段落の枠ごとに読む(ページの切り分けを読み手に任せない。ocr_blocks.py と同じ枠)。
枠は元の PDF の段落の位置(ページの大きさに対する比)。本物は貼り直したページ(rect_*.png)、合成はそのまま。
設定は ocr_doctr.py と同じ(fast_base + crnn_vgg16_bn、既定の assume_straight_pages)。
使い方: .venv_doctr/bin/python -I ocr_doctr_blocks.py <out.jsonl> <tag> <画像...>"""
import sys, os, json, re, time, subprocess
import numpy as np, cv2, torch
from doctr.models import ocr_predictor
HERE=os.path.dirname(os.path.abspath(__file__)); B=os.path.dirname(HERE)
DET,RECO="fast_base","crnn_vgg16_bn"
DEVICE="mps" if torch.backends.mps.is_available() else "cpu"
_boxes={}
def blocks(d):
    if d in _boxes: return _boxes[d]
    xml=subprocess.run(["pdftotext","-bbox-layout",f"{B}/data_smartdoc/Original_documents/page_{d}.pdf","-"],capture_output=True,text=True).stdout
    pg=re.search(r'<page width="([\d.]+)" height="([\d.]+)"',xml); W,H=float(pg.group(1)),float(pg.group(2))
    _boxes[d]=[[float(a)/W,float(b)/H,float(c)/W,float(e)/H] for a,b,c,e in re.findall(r'<block xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"',xml)]
    return _boxes[d]
out,tag,imgs=sys.argv[1],sys.argv[2],sys.argv[3:]
done=set()
if os.path.exists(out):
    for l in open(out): r=json.loads(l); done.add((r["image"],r["tag"]))
todo=[p for p in imgs if (os.path.basename(p),tag) not in done]
print(len(todo),"to read, device",DEVICE,flush=True)
model=ocr_predictor(det_arch=DET,reco_arch=RECO,pretrained=True).to(DEVICE).eval()
m=0.012
for p in todo:
    name=os.path.basename(p); d=re.search(r"_D(\d+)_",name).group(1)
    im=cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB); h,w=im.shape[:2]; crops=[]
    for x0,y0,x1,y1 in blocks(d):
        a,b=max(0,int((x0-m)*w)),max(0,int((y0-m)*h)); c,e=min(w,int((x1+m)*w)),min(h,int((y1+m)*h))
        crops.append(np.ascontiguousarray(im[b:e,a:c]))
    t0=time.time()
    with torch.no_grad(): res=model(crops)
    text="\n".join(pg.render() for pg in res.pages)
    rec=dict(image=name,tag=tag,model="doctr-blocks",model_version=f"doctr {DET}+{RECO} per PDF paragraph box; device={DEVICE}",
             n_blocks=len(crops),text=text,latency_s=round(time.time()-t0,2),ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(out,"a") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    print(name,len(crops),len(text),rec["latency_s"],flush=True)

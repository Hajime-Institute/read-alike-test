# -*- coding: utf-8 -*-
"""段落の枠ごとに読む(ページの切り分けを読み手に任せない)。
ページ全体を Tesseract に読ませると、誤りにページの切り分けの失敗が混ざった(貼り直すと正答率が大きく変わった)。
そこで、元の PDF の文字の位置から取った段落の枠を、本物(貼り直したページ)と合成の両方で
同じ位置から切り出し、枠ごとに psm 6 で読んで、段落の順につなぐ。座標はページの大きさの比で写す。
使い方: python -I ocr_blocks.py <out.jsonl> <tag> <画像...>"""
import sys, os, json, re, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor
import cv2
HERE=os.path.dirname(os.path.abspath(__file__)); B=os.path.dirname(HERE); TESS="/opt/homebrew/bin/tesseract"
_boxes={}
def blocks(d):
    """段落の枠を元の PDF の文字の位置から取る(pdftotext -bbox-layout の block)。ページの大きさに対する比で返す。
    (最初は綺麗な合成を Tesseract で読んで枠を取ったが、薄い青で刷られた段落が拾われず、枠が抜けた)"""
    if d in _boxes: return _boxes[d]
    pdf=f"{B}/data_smartdoc/Original_documents/page_{d}.pdf"
    if not os.path.exists(pdf):   # 元の PDF が無い文書(SmartDoc-QA の 11–30 など): ピントの合った撮影から取った枠を使う(blocks_from_sharp.py)
        _boxes[d]=list(enumerate(json.load(open(f"{B}/results/blocks_sharp.json"))[str(d)])); return _boxes[d]
    xml=subprocess.run(["pdftotext","-bbox-layout",pdf,"-"],capture_output=True,text=True).stdout
    # 文字に & などが混じると XML として読めないので、座標だけを正規表現で取る
    pg=re.search(r'<page width="([\d.]+)" height="([\d.]+)"',xml); W,H=float(pg.group(1)),float(pg.group(2))
    bx=[(i,[float(a)/W,float(b)/H,float(c)/W,float(e)/H]) for i,(a,b,c,e) in
        enumerate(re.findall(r'<block xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"',xml))]
    _boxes[d]=bx; return bx
def read(path,tag):
    name=os.path.basename(path); d=re.search(r"_D(\d+)_",name).group(1); im=cv2.imread(path); H,W=im.shape[:2]
    m=0.012; texts=[]; t0=time.time()
    for _,(x0,y0,x1,y1) in blocks(d):
        a,b=max(0,int((x0-m)*W)),max(0,int((y0-m)*H)); c,e=min(W,int((x1+m)*W)),min(H,int((y1+m)*H))
        ok,enc=cv2.imencode(".png",im[b:e,a:c])
        r=subprocess.run([TESS,"stdin","stdout","-l","eng","--psm","6"],input=enc.tobytes(),capture_output=True)
        texts.append(r.stdout.decode("utf-8","replace").strip())
    return dict(image=name,tag=tag,model="tesseract-blocks",model_version="tesseract 5.5.1 psm6 per paragraph box from clean page",
                n_blocks=len(texts),text="\n".join(texts),latency_s=round(time.time()-t0,1),ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
if __name__=="__main__":
    out,tag,imgs=sys.argv[1],sys.argv[2],sys.argv[3:]
    done=set()
    if os.path.exists(out):
        for l in open(out): r=json.loads(l); done.add((r["image"],r["tag"]))
    todo=[p for p in imgs if (os.path.basename(p),tag) not in done]
    for d in sorted({re.search(r"_D(\d+)_",os.path.basename(p)).group(1) for p in todo}): blocks(d)
    with ThreadPoolExecutor(4) as ex:
        for rec in ex.map(lambda p: read(p,tag), todo):
            with open(out,"a") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")
            print(rec["image"],rec["n_blocks"],len(rec["text"]),flush=True)

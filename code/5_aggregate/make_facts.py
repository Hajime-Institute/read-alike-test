# -*- coding: utf-8 -*-
"""ピンぼけの検査の数を一か所(results/facts_defocus.json)にまとめ、論文の表の行を書き出す。
論文の数は手で写さず、この出力から取る。audit_angles.py を条件(機種・焦点の段階・照明)× 読み手 × 選び方ごとに並列で回す。
使い方: python -I make_facts.py <smartdoc_pilot> <論文の ja ディレクトリ>"""
import sys, os, json, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
B=sys.argv[1]; JA=sys.argv[2]; PY=sys.executable
# 条件: 機種・焦点の段階・照明(L2 昼光と天井灯 / L3 夜と卓上灯 / L4 卓上灯と物の影)。ラベルは「機種 焦点 照明」
CELLS=[(ph,ob,L,f"{lab} {L}") for ph,ob,lab in (("WP","Ob820","Nokia 1"),("WP","Ob940","Nokia 2"),("Android","Ob1","Samsung 1"),("Android","Ob2","Samsung 2")) for L in ("L2","L3","L4")]
READERS=[("tessblk","Tesseract"),("doctrblk","docTR"),("visionblk","Vision")]+([("vlmblk","Mistral")] if os.path.exists(f"{B}/results/raw_vlm_blocks.jsonl") else [])
CORE=[c for c in CELLS if c[0:3] in (("WP","Ob820","L2"),("Android","Ob1","L2"),("Android","Ob2","L2"))]
# 低照度(夜・卓上灯、ピントは合っている): 生成器の組を照明のものにする
LIGHT_CELLS=[("WP","none","L3","Nokia low light"),("Android","none","L3","Samsung low light")]
FAMILY={**{lab:"defocus" for *_,lab in CELLS},**{lab:"lowlight" for *_,lab in LIGHT_CELLS}}   # 文書をまたぐ設定・分けない比べは前の 3 条件だけ
def run(ph,ob,L,rd,xdoc,sel="prof",extra=None,genset=""):
    with tempfile.NamedTemporaryFile(suffix=".json",delete=False) as f: out=f.name
    full=(xdoc=="0" and sel=="prof" and not extra)
    env=dict(os.environ,PH=ph,OB=ob,LIGHT=L,MASK="sharp",XDOC=xdoc,SEL=sel,JSON_OUT=out,NULL="1" if full else "0",POS="1" if full else "0",GENSET=genset,**(extra or {}))
    subprocess.run([PY,"-I",f"{B}/code/audit_angles.py",B,rd],env=env,check=True,capture_output=True)
    return json.load(open(out,encoding="utf-8"))
jobs=[]
for ph,ob,L,lab in CELLS:
    for rd,rl in READERS:
        jobs.append(("per_capture",f"{lab}|{rl}",(ph,ob,L,rd,"0")))
        jobs.append(("per_capture_select_by_accuracy",f"{lab}|{rl}",(ph,ob,L,rd,"0","acc")))
        if (ph,ob,L,lab) in CORE:
            jobs.append(("cross_document",f"{lab}|{rl}",(ph,ob,L,rd,"1")))
            jobs.append(("per_capture_docs_6_10",f"{lab}|{rl}",(ph,ob,L,rd,"0","prof",{"DOCS":"6-10"})))
for ph,ob,L,lab in LIGHT_CELLS:
    for rd,rl in READERS:
        jobs.append(("per_capture",f"{lab}|{rl}",(ph,ob,L,rd,"0","prof",None,"light")))
        jobs.append(("per_capture_select_by_accuracy",f"{lab}|{rl}",(ph,ob,L,rd,"0","acc",None,"light")))
F={k:{} for k in ("per_capture","per_capture_select_by_accuracy","cross_document","per_capture_docs_6_10")}
def go(j):
    key,cell,args=j
    try: return key,cell,run(*args)
    except subprocess.CalledProcessError as e: return key,cell,{"error":e.stderr.decode()[-300:]}
with ThreadPoolExecutor(8) as ex:
    for key,cell,res in ex.map(go,jobs): F[key][cell]=res; print(key,cell,"error" if "error" in res else "ok",flush=True)
F["cells"]=[lab for *_,lab in CELLS]+[lab for *_,lab in LIGHT_CELLS]; F["readers"]=[rl for _,rl in READERS]; F["family"]=FAMILY
json.dump(F,open(f"{B}/results/facts_defocus.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
# 表の行は write_tables.py が書き出す(日本語版と英語版)
EN=os.path.join(os.path.dirname(JA.rstrip("/")),"en")
for d,lang in ((JA,"ja"),(EN,"en")):
    if os.path.isdir(d): subprocess.run([PY,"-I",f"{B}/code/write_tables.py",f"{B}/results/facts_defocus.json",d,lang],check=True)
print("ok")

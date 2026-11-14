# -*- coding: utf-8 -*-
"""撮影の角度ごとに、ページを上から 5 つに分けた帯の語の正答率(綺麗な合成と鮮明な撮影の両方で読めた語)を文書で平均する。
設計の感度(design_sensitivity.py)で本物の撮影が落ちたのが逆向きに傾いた一枚(a5_b10)だけだったので、その一枚が違う所で語を落とすかを見るため。
本文の「12 の条件のうち 9 で、上の帯に比べた下の帯の正答率が組の中で最も高い」は、この出力の 下の帯 − 上の帯 から数えた(Tesseract)。
使い方: python -I angle_bands.py <読みと正解のあるディレクトリ> <tessblk|doctrblk|visionblk> <PH> <OB> <LIGHT>"""
import sys, os, json, re, statistics as st, collections
B=sys.argv[1]; READER=sys.argv[2]; PH,OB,LIGHT=sys.argv[3:6]
sys.path.insert(0,B+"/code"); from score_words import read_vector
FN={"tessblk":"raw_tess_blocks.jsonl","doctrblk":"raw_doctr_blocks.jsonl","visionblk":"raw_vision_blocks.jsonl"}[READER]
T={}
for l in open(f"{B}/results/{FN}"):
    r=json.loads(l)
    if r["tag"]!="blocks": continue
    k=r["image"].rsplit(".",1)[0]
    if k in T: continue
    if not (k.startswith("rect_") or k.startswith("syn_D")): continue
    d=re.search(r"_D(\d+)_",k).group(1); T[k]=read_vector(open(f"{B}/data_smartdoc/Ground_truth/page_{d}.txt",encoding="utf-8").read(),r["text"])[1]
NB=5; prof=collections.defaultdict(list)
for k,v in T.items():
    m=re.match(rf"rect_(S|M)_Img_{PH}_D(\d+)_{LIGHT}_r35_(a-?\d+_b-?\d+)_{OB}$",k)
    if not m: continue
    d=int(m.group(2)); cl=T.get(f"syn_D{d}_{PH}_none_0"); sh=T.get(f"rect_S_Img_{PH}_D{d}_L2_r35_a0_b0")
    if cl is None or sh is None or len(cl)!=len(v) or len(sh)!=len(v): continue
    n=len(v); idx=[i for i in range(n) if cl[i] and sh[i]]
    bins=[[] for _ in range(NB)]
    for i in idx: bins[min(NB-1,i*NB//n)].append(v[i])
    prof[m.group(1)+"_"+m.group(3)].append([sum(b)/len(b) if b else float("nan") for b in bins])
for a,ps in sorted(prof.items()):
    print(f"{a:12s} docs={len(ps):2d} " + " ".join(f"{st.mean([p[j] for p in ps if p[j]==p[j]]):.2f}" for j in range(NB)))

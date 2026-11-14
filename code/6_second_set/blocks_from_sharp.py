# -*- coding: utf-8 -*-
"""元の PDF が無い文書(SmartDoc-QA の 11–30 など)の段落の枠を、貼り直したピントの合った正面の撮影から取る。
Tesseract(psm 3)のブロック(level 2)の枠を、ページの大きさに対する比で書き出す。語の無いブロック(罫線・署名など)は外す。
使い方: python -I blocks_from_sharp.py <out.json> <貼り直したピントの合った撮影...>(名前の _D<番号>_ で文書を決める。同じ文書が複数あれば最初のもの)"""
import sys, os, re, json, subprocess
TESS = "/opt/homebrew/bin/tesseract"
out = sys.argv[1]; res = json.load(open(out)) if os.path.exists(out) else {}
for p in sys.argv[2:]:
    d = re.search(r"_D(\d+)_", os.path.basename(p)).group(1)
    if d in res: continue
    tsv = subprocess.run([TESS, p, "stdout", "-l", "eng", "--psm", "3", "tsv"], capture_output=True, text=True).stdout.splitlines()
    hdr = tsv[0].split("\t"); rows = [dict(zip(hdr, l.split("\t"))) for l in tsv[1:] if l.count("\t") >= 11]
    W = H = None; blocks = {}
    for r in rows:
        if r["level"] == "1": W, H = float(r["width"]), float(r["height"])
        if r["level"] == "2": blocks[r["block_num"]] = [float(r["left"]), float(r["top"]), float(r["left"]) + float(r["width"]), float(r["top"]) + float(r["height"])]
    words = {}
    for r in rows:
        if r["level"] == "5" and re.search(r"[A-Za-z0-9]{2,}", r.get("text", "")) and float(r.get("conf", "-1")) > 30:
            words[r["block_num"]] = words.get(r["block_num"], 0) + 1
    bx = [[b[0] / W, b[1] / H, b[2] / W, b[3] / H] for k, b in sorted(blocks.items(), key=lambda kv: int(kv[0])) if words.get(k, 0) >= 1]
    res[d] = bx; print(d, os.path.basename(p), len(bx), "blocks", flush=True)
json.dump(res, open(out, "w"), indent=1)

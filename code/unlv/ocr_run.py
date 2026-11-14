# -*- coding: utf-8 -*-
"""実画像(2B/3B/3A/4B)と合成 200 dpi を Tesseract で読み、results/ocr_<set>_<cond>.jsonl に追記する。
既に読んだページは飛ばす(ページ数を増やすときに読み直さない)。

合成 200 dpi(cond = syn_s<sigma>_t<T>)の作り方(4B = 400 dpi 二値スキャンから):
  1. 4B を 0/255 の濃淡にする(白 = 255)
  2. sigma > 0 ならガウスぼかし。sigma は出力 200 dpi の画素単位で、400 dpi 上では 2*sigma を掛ける
     (cv2.GaussianBlur, ksize=(0,0) で自動, float32)
  3. cv2.resize(INTER_AREA) で縦横ちょうど 1/2(2x2 の面積平均)
  4. 大域しきい値: 値 > T を白、それ以外を黒(cv2.THRESH_BINARY と同じ)
  ゾーンは 4B の .uzn 座標を 1/2 して整数に切り捨て。
naive 基準 = sigma 0, T 128(ぼかしなしの面積平均 2x 縮小 + 128 で二値化)= 格子の (0, 128) と同じ画像。

使い方: python -I ocr_run.py <set> <npages>[:cal|:eval] <cond> [<cond> ...]
  cond: 2B 3B 3A 4B syn_s<sigma>_t<T> grid(= 16 格子すべて)
  <npages>:cal / :eval は split.py の文書単位の分割のうち片方だけを読む(格子は校正側だけ読めば足りる)"""
import sys, os, json
from concurrent.futures import ProcessPoolExecutor
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

SIGMAS = [0.0, 0.5, 1.0, 1.5]
THRS = [96, 128, 160, 192]


def cond_name(s, t):
    return f"syn_s{s:.1f}_t{t}"


def parse_syn(cond):
    a, b = cond[len("syn_s"):].split("_t")
    return float(a), int(b)


def synth200(gray4, sigma, T):
    g = gray4.astype(np.float32)
    if sigma > 0:
        g = cv2.GaussianBlur(g, (0, 0), 2.0 * sigma)
    H, W = g.shape
    sm = cv2.resize(g, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    return np.where(sm > T, 255, 0).astype(np.uint8)


def job(args):
    tset, cond, pid, sub = args
    if cond.startswith("syn_"):
        s, t = parse_syn(cond)
        tif, uzn, txt = paths(tset, "4B", pid, sub)
        img = synth200(load_gray(tif), s, t)
        zones = read_uzn(uzn)
        z = ocr_page(img, zones, 200, scale=0.5)
        dpi = 200
    else:
        tif, uzn, txt = paths(tset, cond, pid, sub)
        img, fx = apply_fix(tset, cond, pid, load_gray(tif))
        dpi = DPI[cond]
        z = ocr_page(img, read_uzn(uzn), dpi)
        if fx:
            return {"set": tset, "page": pid, "sub": sub, "cond": cond, "dpi": dpi,
                    "img_shape": list(img.shape), "zones": z, "orientation_fix": fx,
                    "text": "\n".join(r["text"] for r in z)}
    return {"set": tset, "page": pid, "sub": sub, "cond": cond, "dpi": dpi,
            "img_shape": list(img.shape), "zones": z,
            "text": "\n".join(r["text"] for r in z)}


def main():
    tset, npart = sys.argv[1], sys.argv[2]
    n, part = (npart.split(":") + ["all"])[:2]
    n = int(n)
    conds = []
    for c in sys.argv[3:]:
        conds += [cond_name(s, t) for s in SIGMAS for t in THRS] if c == "grid" else [c]
    pages = sample_pages(tset, n)
    if part != "all":
        from split import split_pages
        cal, ev = split_pages([p for p, _ in pages])
        keep = set(cal if part == "cal" else ev)
        pages = [(p, s) for p, s in pages if p in keep]
    jobs, outs = [], {}
    for c in conds:
        out = os.path.join(RES, f"ocr_{tset}_{c}.jsonl")
        done = {r["page"] for r in read_jsonl(out)} if os.path.exists(out) else set()
        outs[c] = out
        jobs += [(tset, c, pid, sub) for pid, sub in pages if pid not in done]
    print(f"{len(jobs)} page-jobs", flush=True)
    with ProcessPoolExecutor(max_workers=int(os.environ.get("OCR_WORKERS", "9"))) as ex:
        for k, rec in enumerate(ex.map(job, jobs, chunksize=1)):
            with open(outs[rec["cond"]], "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if (k + 1) % 20 == 0:
                print(k + 1, flush=True)


if __name__ == "__main__":
    main()

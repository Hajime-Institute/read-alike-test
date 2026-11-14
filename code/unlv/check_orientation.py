# -*- coding: utf-8 -*-
"""各解像度の画像が 3B と同じ向きか(180 度回っていないか)を調べる。
mag 8086_033 の 3A が上下逆に配布されていた(3A の正答率 0.003)ため、同じ原因を標本の全ページで探す。
方法: 3B と比べる画像をどちらも 75 dpi 相当に縮め、そのままと 180 度回したものとで
位相相関の応答(cv2.phaseCorrelate)と、ずらして重ねたときの相関係数を比べる。
出力: results/orientation_<set>.json  {page: {res: {"r0", "r180", "corr0", "corr180", "rot180", "shift"}}}
使い方: python -I check_orientation.py <set> <npages>"""
import sys, os, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

tset, n = sys.argv[1], int(sys.argv[2])


def small(res, pid, sub, shape75=None):
    g = load_gray(paths(tset, res, pid, sub)[0]).astype(np.float32)
    f = 75.0 / DPI[res]
    s = cv2.resize(g, (int(round(g.shape[1] * f)), int(round(g.shape[0] * f))), interpolation=cv2.INTER_AREA)
    s = 255 - s
    if shape75 is not None:
        H, W = shape75
        out = np.zeros((H, W), np.float32)
        h, w = min(H, s.shape[0]), min(W, s.shape[1])
        out[:h, :w] = s[:h, :w]
        s = out
    return s


def score(a, b):
    win = cv2.createHanningWindow((a.shape[1], a.shape[0]), cv2.CV_32F)
    (dx, dy), r = cv2.phaseCorrelate(a, b, win)
    M = np.float32([[1, 0, -dx], [0, 1, -dy]])
    bb = cv2.warpAffine(b, M, (b.shape[1], b.shape[0]))
    c = float(np.corrcoef(a.ravel(), bb.ravel())[0, 1])
    return float(r), c, [float(dx), float(dy)]


out = {}
for pid, sub in sample_pages(tset, n):
    ref = small("3B", pid, sub)
    out[pid] = {}
    for res in ["2B", "4B", "3A"]:
        if not os.path.exists(paths(tset, res, pid, sub)[0]):
            continue
        im = small(res, pid, sub, ref.shape)
        r0, c0, s0 = score(ref, im)
        r1, c1, s1 = score(ref, cv2.rotate(im, cv2.ROTATE_180))
        out[pid][res] = {"r0": r0, "r180": r1, "corr0": c0, "corr180": c1, "rot180": c1 > c0, "shift75": s0 if c0 >= c1 else s1}
    flag = [r for r, v in out[pid].items() if v["rot180"]]
    lowc = [f"{r}:{v['corr0']:.2f}" for r, v in out[pid].items() if max(v["corr0"], v["corr180"]) < 0.6]
    if flag or lowc:
        print(pid, "rot180:", flag, "low corr:", lowc, flush=True)
with open(os.path.join(RES, f"orientation_{tset}.json"), "w") as f:
    json.dump(out, f, indent=1)
print("pages checked", len(out))

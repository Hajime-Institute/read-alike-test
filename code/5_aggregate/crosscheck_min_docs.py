# -*- coding: utf-8 -*-
"""読み手を使う下限(文書の数)を片方の機種の本物の撮影だけで決め、もう片方の機種で本物の撮影が落ちないかを確かめる。
下限の候補ごとに、機種ごとの本物の撮影の判定(一枚ずつ取り出したもの)の落ちた数を数える。
決め方は本文と同じ: 本物の撮影が一つも落ちない最小の下限。読み手をまとめた判定と、読み手ごとの判定の両方で数える。
落ちるかどうかだけを見るので、帰無の対照の決まり(通るを決まらないに下げる)は数に影響しない。
使い方: python -I crosscheck_min_docs.py <facts_defocus.json>"""
import sys, json
F = json.load(open(sys.argv[1], encoding="utf-8"))
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reader_rule import NULL_RULE, base_usable, usable_self   # 規則 b(2026-11-14): その条件で帰無を落とせない読み手は使わない
CELLS = [c for c in F["cells"] if F.get("family", {}).get(c, "defocus") == "defocus"]; READERS = F["readers"]
def combine(vs):
    vs = [v for v in vs if v]
    if not vs: return None
    return "落ちる" if "落ちる" in vs else ("通る" if all(v == "通る" for v in vs) else "決まらない")
def tally(phone, t):
    comb = []; per = []; nuse = 0
    for c in CELLS:
        if not c.startswith(phone): continue
        R = {}
        for rl in READERS:
            P = F["per_capture"].get(f"{c}|{rl}", {})
            if not ("gens" in P and P.get("n_captures", 0) >= 4 and P.get("n_docs", 0) >= t): continue
            if NULL_RULE == "b" and P["gens"].get("null_band", {}).get("verdict") != "落ちる": continue   # 規則 b
            nuse += 1
            for ro, x in P.get("roles", {}).items(): R.setdefault(ro, []).append(x["verdict"]); per.append(x["verdict"])
        comb += [combine(v) for v in R.values()]
    return comb.count("落ちる"), len(comb), per.count("落ちる"), len(per), nuse
print("下限  機種     まとめた判定で落ちた数/取り出し方  読み手ごとに落ちた数/判定  使えた読み手×条件")
for t in range(2, 8):
    for ph in ("Nokia", "Samsung"):
        fc, nc, fp, npr, nu = tally(ph, t)
        print(f"{t:3d}  {ph:8s} {fc:3d}/{nc:3d}                         {fp:3d}/{npr:3d}                {nu}")
def pick(ph):   # 本物の撮影が(読み手ごとにも)一つも落ちない最小の下限
    for t in range(2, 11):
        fc, _, fp, _, _ = tally(ph, t)
        if fc == 0 and fp == 0: return t
for a, b in (("Nokia", "Samsung"), ("Samsung", "Nokia")):
    t = pick(a); fc, nc, fp, npr, nu = tally(b, t)
    print(f"{a} だけで決めた下限 = 文書 {t} 件 → {b} で落ちた数: まとめて {fc}/{nc}、読み手ごと {fp}/{npr}")

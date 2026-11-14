# -*- coding: utf-8 -*-
"""忠実さの分かっている生成器(本物の撮影を割合 p だけ帰無の対照に置き換えたもの)の判定を、本文と同じ決まりで数える。
読み手は検査画像 4 枚以上・文書 5 件以上の条件でだけ使い、まとめた判定は「一人でも落とせば落ちる・全員で通れば通る」。
帰無の対照がまとめて落ちない条件では、通るを決まらないにする。p ごとに、本物の撮影を一枚ずつ取り出した 64 通りの判定、
κ の差の平均、撮り直しに対する読めない語の重なり(F1)の比の平均を出す。
使い方: python -I mix_summary.py <out_mix のディレクトリ> [out.json]"""
import sys, os, json, glob, collections, statistics as st
D = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else None
CELL = {("WP", "Ob820"): "Nokia 1", ("WP", "Ob940"): "Nokia 2", ("Android", "Ob1"): "Samsung 1", ("Android", "Ob2"): "Samsung 2"}
RD = {"tessblk": "Tesseract", "doctrblk": "docTR", "visionblk": "Vision", "vlmblk": "Mistral"}
F = collections.defaultdict(dict)
for p in glob.glob(os.path.join(D, "*.json")):
    b = os.path.basename(p)[:-5].split("_")
    if len(b) != 4: continue
    ph, ob, L, rd = b; F[f"{CELL[(ph, ob)]} {L}"][RD[rd]] = json.load(open(p, encoding="utf-8"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reader_rule import NULL_RULE, base_usable, usable_self   # 規則 b(2026-11-14): その条件で帰無を落とせない読み手は使わない
def usable(P): return usable_self(P)
def combine(vs):
    vs = [v for v in vs if v]
    if not vs: return None
    return "落ちる" if "落ちる" in vs else ("通る" if all(v == "通る" for v in vs) else "決まらない")
ps = sorted({float(k.split("|")[1]) for c in F.values() for P in c.values() for k in P.get("mix", {})})
res = {}
for p in ps:
    comb = []; diffs = []; ratios = []; per = collections.Counter()
    for c, Rs in F.items():
        Ps = {rl: P for rl, P in Rs.items() if usable(P)}
        nv = combine([P["gens"]["null_band"]["verdict"] for P in Ps.values() if "null_band" in P.get("gens", {})])
        adj = lambda v: "決まらない" if (nv != "落ちる" and v == "通る") else v
        R = collections.defaultdict(list)
        for rl, P in Ps.items():
            for k, x in P.get("mix", {}).items():
                role, pp = k.rsplit("|", 1)
                if abs(float(pp) - p) > 1e-9: continue
                v = adj(x["verdict"]); R[role].append(v); per[(rl, v)] += 1; diffs.append(x["diff"]["mean"])
                if x.get("dice_mix") is not None and x.get("dice_rec"): ratios.append(x["dice_mix"] / x["dice_rec"])
        comb += [combine(v) for v in R.values()]
    t = {v: comb.count(v) for v in ("通る", "決まらない", "落ちる")}
    res[p] = {"combined": t, "n": len(comb), "mean_diff": st.mean(diffs), "f1_ratio": st.mean(ratios),
              "per_reader": {rl: [per[(rl, v)] for v in ("通る", "決まらない", "落ちる")] for rl in RD.values()}}
    print(f"p={p:.1f}  通る/決まらない/落ちる {t['通る']:2d}/{t['決まらない']:2d}/{t['落ちる']:2d} (計 {len(comb)})  κ差 {st.mean(diffs):+.3f}  F1 比 {st.mean(ratios):.2f}")
if OUT: json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

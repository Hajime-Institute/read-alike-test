# -*- coding: utf-8 -*-
"""二つ目のセット(SmartDoc-QA の古い事務文書 11–20)の検査の結果を、本文と同じ決まりで数える。
読み手は検査画像 4 枚以上・文書 5 件以上の条件でだけ使い、まとめた判定は「一人でも落とせば落ちる・全員で通れば通る」。
帰無の対照が(まとめて)落ちない条件では、帰無そのもの以外の通るを決まらないにする。
使い方: python -I letters_summary.py <results/audit のディレクトリ> [facts の書き出し先]"""
import sys, os, json, glob, collections, statistics as st
D = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else None
CELL = {("WP", "Ob820"): "Nokia 1", ("WP", "Ob940"): "Nokia 2", ("Android", "Ob1"): "Samsung 1", ("Android", "Ob2"): "Samsung 2"}
RD = {"tessblk": "Tesseract", "doctrblk": "docTR", "visionblk": "Vision", "vlmblk": "Mistral"}
F = {"per_capture": {}, "cells": [], "readers": []}
for p in sorted(glob.glob(os.path.join(D, "*.json"))):
    ph, ob, L, rd = os.path.basename(p)[:-5].split("_")
    c = f"{CELL[(ph, ob)]} {L}"; F["per_capture"][f"{c}|{RD[rd]}"] = json.load(open(p, encoding="utf-8"))
    if c not in F["cells"]: F["cells"].append(c)
    if RD[rd] not in F["readers"]: F["readers"].append(RD[rd])
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "5_aggregate"))   # reader_rule.py
from reader_rule import NULL_RULE, usable_self   # 規則 b(2026-11-14)
def usable(P): return usable_self(P)
def combine(vs):
    vs = [v for v in vs if v]
    if not vs: return None
    return "落ちる" if "落ちる" in vs else ("通る" if all(v == "通る" for v in vs) else "決まらない")
t = lambda vs: "/".join(str(vs.count(v)) for v in ("通る", "決まらない", "落ちる"))
real = []; nul = []; rows = []; per_reader_real = collections.Counter(); pairs = 0; ks = collections.defaultdict(list)
for c in F["cells"]:
    Ps = {rl: F["per_capture"][f"{c}|{rl}"] for rl in F["readers"] if usable(F["per_capture"].get(f"{c}|{rl}", {}))}
    pairs += len(Ps)
    nv = combine([P["gens"]["null_band"]["verdict"] for P in Ps.values() if "null_band" in P.get("gens", {})])
    def adj(v): return "決まらない" if (nv != "落ちる" and v == "通る") else v
    R = collections.defaultdict(list)
    for rl, P in Ps.items():
        ks["recapture"].append(P["ceiling"]["mean"])
        if "null_band" in P["gens"]: ks["null"].append(P["gens"]["null_band"]["kappa"]["mean"])
        for ro, x in P.get("roles", {}).items():
            v = adj(x["verdict"]); R[ro].append(v); per_reader_real[(rl, v)] += 1
    rv = [combine(v) for v in R.values()]; real += rv; nul.append(nv)
    rows.append(f"{c:14s} readers {','.join(Ps) or '-':28s} null {nv or '-':6s} real {t(rv)}")
print("\n".join(rows))
print(f"\n使えた読み手と条件の組: {pairs}")
print(f"本物の撮影(まとめた判定、通る/決まらない/落ちる): {t(real)}  (計 {len(real)})")
print("読み手ごとの本物の撮影:", {rl: "/".join(str(per_reader_real[(rl, v)]) for v in ("通る", "決まらない", "落ちる")) for rl in F["readers"]})
print(f"帰無の対照(条件、通る/決まらない/落ちる): {t([v for v in nul if v])}  (使えた条件 {len([v for v in nul if v])})")
print("κ の平均: 撮り直し %.3f  帰無 %.3f" % (st.mean(ks["recapture"]) if ks["recapture"] else float("nan"), st.mean(ks["null"]) if ks["null"] else float("nan")))
if OUT: json.dump(F, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

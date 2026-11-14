# -*- coding: utf-8 -*-
"""許す幅 δ を何倍かにしたとき、判定の数がどう変わるかを見る(δ の感度)。
facts_defocus.json に残した差の 95% 区間を、幅 s·δ で判定し直す(下端 > −s·δ で通る、上端 < −s·δ で落ちる)。
読み手の決まり・帰無の対照の決まり(帰無が落ちない条件では通るを決まらないにする)は write_tables.py と同じ。
数えるのは、生成器と選び方の 88 通り(帰無を除く)・帰無の対照の条件・本物の撮影を一枚ずつ取り出した 64 通り。
使い方: python -I sensitivity_delta.py <facts_defocus.json> [倍率 ...]"""
import sys, json, os
F = json.load(open(sys.argv[1], encoding="utf-8")); SCALES = [float(x) for x in sys.argv[2:]] or [0.5, 1.0, 2.0]
LO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "facts_lodo.json"), encoding="utf-8"))
for k, P in F["per_capture"].items():
    A = F["per_capture_select_by_accuracy"].get(k, {})
    if "gens" in P and "ours_plane" in A.get("gens", {}): P["gens"]["ours_plane_acc"] = A["gens"]["ours_plane"]
    Q = LO.get(k, {})
    if "gens" in P and "ours_plane" in Q.get("gens", {}): P["gens"]["ours_plane_fixed"] = Q["gens"]["ours_plane"]
CELLS = [c for c in F["cells"] if F.get("family", {}).get(c, "defocus") == "defocus"]; READERS = F["readers"]
GENS = ["ours_plane", "ours_plane_acc", "ours_plane_fixed", "ours_lampdef", "ours_uni", "albDefocus", "albGauss", "augDepth"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reader_rule import NULL_RULE, base_usable, usable_self   # 規則 b(2026-11-14): その条件で帰無を落とせない読み手は使わない
def usable(P): return base_usable(P)
def combine(vs):
    vs = [v for v in vs if v]
    if not vs: return None
    return "落ちる" if "落ちる" in vs else ("通る" if all(v == "通る" for v in vs) else "決まらない")
def judge(ci, d): return "通る" if ci[0] > -d else ("落ちる" if ci[1] < -d else "決まらない")
print("倍率  生成器 88 通り(通る/決まらない/落ちる)  帰無の対照(通る/決まらない/落ちる)  本物 64 通り(通る/決まらない/落ちる)  通った生成器")
for s in SCALES:
    gen = []; nul = []; real = []; passed = []
    for c in CELLS:
        Ps = {rl: F["per_capture"][f"{c}|{rl}"] for rl in READERS if usable(F["per_capture"].get(f"{c}|{rl}", {}))}
        if NULL_RULE == "b": Ps = {rl: P for rl, P in Ps.items() if "null_band" in P["gens"] and judge(P["gens"]["null_band"]["diff"]["ci"], s * P["delta"]) == "落ちる"}   # 倍率ごとに帰無を落とせる読み手だけ
        if not Ps: continue
        nv = combine([judge(P["gens"]["null_band"]["diff"]["ci"], s * P["delta"]) for P in Ps.values() if "null_band" in P["gens"]])
        nul.append(nv)
        def adj(v): return "決まらない" if (nv != "落ちる" and v == "通る") else v
        for g in GENS:
            v = combine([adj(judge(P["gens"][g]["diff"]["ci"], s * P["delta"])) for P in Ps.values() if g in P["gens"]])
            if v: gen.append(v)
            if v == "通る": passed.append(f"{c}:{g}")
        R = {}
        for P in Ps.values():
            for ro, x in P.get("roles", {}).items(): R.setdefault(ro, []).append(adj(judge(x["diff"]["ci"], s * P["delta"])))
        real += [combine(v) for v in R.values()]
    t = lambda vs: "/".join(str(vs.count(v)) for v in ("通る", "決まらない", "落ちる"))
    print(f"{s:4.2f}  {t(gen)} (計 {len(gen)})  {t(nul)}  {t(real)} (計 {len(real)})  {', '.join(passed) or 'なし'}")

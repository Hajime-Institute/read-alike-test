# -*- coding: utf-8 -*-
"""design_sensitivity.py の出力を、本文と同じ決まりで数える。
読み手は検査画像 4 枚以上・文書 5 件以上の条件でだけ使い、読み手をまとめた判定は「一人でも落とせば落ちる・全員で通れば通る」。
帰無の対照が(読み手をまとめて)落ちない条件では、帰無そのもの以外の通るを決まらないにする(write_tables.py と同じ)。
数えるのは、本物の撮影を一枚ずつ取り出した判定(本文では 64 通り)・帰無の対照の条件(12)・生成器と選び方の組み合わせ(88)。
あわせて、使えた読み手と条件の組の数、生成器ごとの本物との κ の平均(帰無・撮り直しも)を出す。
使い方: python -I design_sensitivity_summary.py <facts_*.json ...> [--base facts_defocus.json facts_lodo.json]"""
import sys, json, os, statistics as st
args = sys.argv[1:]; BASE = None
if "--base" in args: i = args.index("--base"); BASE = args[i + 1:i + 3]; del args[i:i + 3]
GENS = ["ours_plane", "ours_plane_acc", "ours_plane_fixed", "ours_lampdef", "ours_uni", "albDefocus", "albGauss", "augDepth"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reader_rule import NULL_RULE, base_usable, usable_self   # 規則 b(2026-11-14): その条件で帰無を落とせない読み手は使わない
def usable(P): return usable_self(P)   # 規則 b なら、その版の帰無を落とせる読み手だけ
def combine(vs):
    vs = [v for v in vs if v]
    if not vs: return None
    return "落ちる" if "落ちる" in vs else ("通る" if all(v == "通る" for v in vs) else "決まらない")
def merged(F, LO=None):
    LO = LO if LO is not None else F.get("lodo", {})
    M = {}
    for k, P in F["per_capture"].items():
        P = json.loads(json.dumps(P))
        A = F["per_capture_select_by_accuracy"].get(k, {}); Q = LO.get(k, {})
        if "gens" in P and "ours_plane" in A.get("gens", {}): P["gens"]["ours_plane_acc"] = A["gens"]["ours_plane"]
        if "gens" in P and "ours_plane" in Q.get("gens", {}): P["gens"]["ours_plane_fixed"] = Q["gens"]["ours_plane"]
        M[k] = P
    return M
def count(F, M):
    CELLS = [c for c in F["cells"] if F.get("family", {}).get(c, "defocus") == "defocus"]; READERS = F["readers"]
    gen = []; nul = []; real = []; passed = []; pairs = 0; ks = {}
    verdicts = {}
    for c in CELLS:
        Ps = {rl: M[f"{c}|{rl}"] for rl in READERS if usable(M.get(f"{c}|{rl}", {}))}
        pairs += len(Ps)
        for P in Ps.values():
            ks.setdefault("recapture", []).append(P["ceiling"]["mean"] if "ceiling" in P else float("nan"))
            for g, x in P["gens"].items():
                if "kappa" in x: ks.setdefault(g, []).append(x["kappa"]["mean"] if isinstance(x["kappa"], dict) else x["kappa"])
        nv = combine([P["gens"]["null_band"]["verdict"] for P in Ps.values() if "null_band" in P["gens"]])
        nul.append(nv); verdicts[(c, "null_band")] = nv
        def adj(v): return "決まらない" if (nv != "落ちる" and v == "通る") else v
        for g in GENS:
            v = combine([adj(P["gens"][g]["verdict"]) for P in Ps.values() if g in P["gens"]])
            if v: gen.append(v); verdicts[(c, g)] = v
            if v == "通る": passed.append(f"{c}:{g}")
        R = {}
        for P in Ps.values():
            for ro, x in P.get("roles", {}).items(): R.setdefault(ro, []).append(adj(x["verdict"]))
        real += [combine(v) for v in R.values()]
    t = lambda vs: "/".join(str(vs.count(v)) for v in ("通る", "決まらない", "落ちる"))
    return {"pairs": pairs, "gen": t(gen), "ngen": len(gen), "null": t(nul), "real": t(real), "nreal": len(real), "passed": passed, "verdicts": verdicts,
            "kappa": {g: (st.mean([x for x in v if x == x]) if any(x == x for x in v) else float("nan")) for g, v in ks.items()}}
rows = []
if BASE:
    F = json.load(open(BASE[0], encoding="utf-8")); LO = json.load(open(BASE[1], encoding="utf-8"))
    rows.append(("本文(facts_defocus)", count(F, merged(F, LO))))
for p in args:
    F = json.load(open(p, encoding="utf-8")); v = F.get("variant", {})
    rows.append((v.get("name", os.path.basename(p)) + " " + " ".join(f"{k}={x}" for k, x in v.items() if k != "name"), count(F, merged(F))))
print(f"{'設定':28s} {'組':>3s}  {'本物(通/決/落)':16s} {'帰無(通/決/落)':12s} {'生成器(通/決/落)':18s} 通った生成器")
for name, r in rows:
    print(f"{name:28s} {r['pairs']:3d}  {r['real']:>9s} ({r['nreal']:2d})  {r['null']:>10s}  {r['gen']:>10s} ({r['ngen']})  {', '.join(r['passed']) or 'なし'}")
print("\n本物との κ の平均(使えた読み手と条件の組)")
keys = ["recapture", "ours_plane", "ours_plane_acc", "null_band", "ours_uni", "albDefocus", "albGauss", "augDepth"]
print(f"{'設定':28s} " + " ".join(f"{k[:10]:>10s}" for k in keys))
for name, r in rows:
    print(f"{name:28s} " + " ".join(f"{r['kappa'].get(k, float('nan')):10.3f}" for k in keys))
if BASE and len(rows) > 1:
    b = rows[0][1]["verdicts"]
    for name, r in rows[1:]:
        if name.startswith("base"):
            diff = [k for k in set(b) | set(r["verdicts"]) if b.get(k) != r["verdicts"].get(k)]
            print(f"\n{name} と本文の判定の食い違い: {len(diff)}", diff[:10])

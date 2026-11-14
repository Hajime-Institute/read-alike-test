# -*- coding: utf-8 -*-
"""facts_defocus.json から論文の表の行を書き出す。日本語版(ja)と英語版(en)で、ラベルだけが違う。
条件が多い(機種・焦点の段階・照明)ので、表は条件をまとめた数にし、条件ごとの判定は図(make_fig_grid.py)で見せる。
使い方: python -I write_tables.py <facts_defocus.json> <出力ディレクトリ> <ja|en>"""
import sys, json, statistics as st
F = json.load(open(sys.argv[1], encoding="utf-8")); OUTD = sys.argv[2]; LANG = sys.argv[3]
CELLS = F["cells"]; READERS = F["readers"]
L = {"ja": {"ours_plane_fixed": "傾いた紙のぼけ（ほかの文書で選ぶ）", "ours_plane_acc": "傾いた紙のぼけ（正答率で選ぶ）", "null_band": "帰無の対照（帯の正答率どおり）", "ours_plane": "傾いた紙のぼけ", "ours_uni": "一様な円のぼけ",
            "albDefocus": "albumentations Defocus", "albGauss": "albumentations GaussianBlur", "augDepth": "Augraphy DepthSimulatedBlur",
            "roles": "本物の撮影（一枚ずつ）", "all": "全体", "通る": "通る", "落ちる": "落ちる", "決まらない": "決まらない",
            "ours_lampdef": "傾いた紙のぼけ＋卓上灯", "L_ours_plane": "卓上灯の撮影", "L_ours_plane_acc": "卓上灯の撮影（正答率で選ぶ）", "L_ours_grad": "照明の傾きだけ", "L_ours_uni": "一様な暗さ", "L_albBright": "albumentations RandomBrightnessContrast", "L_augLight": "Augraphy LightingGradient"},
     "en": {"ours_plane_fixed": "Tilted-page defocus (set on other documents)", "ours_plane_acc": "Tilted-page defocus (accuracy-based)", "null_band": "Null baseline (band-matched random dropout)", "ours_plane": "Tilted-page defocus", "ours_uni": "Uniform disk blur",
            "albDefocus": "albumentations Defocus", "albGauss": "albumentations GaussianBlur", "augDepth": "Augraphy DepthSimulatedBlur",
            "roles": "Real capture (one at a time)", "all": "All", "通る": "pass", "落ちる": "fail", "決まらない": "undecided",
            "ours_lampdef": "Tilted-page defocus + desk lamp", "L_ours_plane": "Desk-lamp capture", "L_ours_plane_acc": "Desk-lamp capture (accuracy-based)", "L_ours_grad": "Lighting gradient only", "L_ours_uni": "Uniform darkening", "L_albBright": "albumentations RandomBrightnessContrast", "L_augLight": "Augraphy LightingGradient"}}[LANG]
FAM = F.get("family", {})
import os
# 設定を一つに固定した判定(確かめる文書を除いて選ぶ。run_lodo.py の results/facts_lodo.json)を、傾いた紙のぼけの一つの行として表 3 に入れる
LO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "facts_lodo.json"), encoding="utf-8"))
for k, Q in LO.items():
    P = F["per_capture"].get(k, {})
    if "gens" in P and "ours_plane" in Q.get("gens", {}): P["gens"]["ours_plane_fixed"] = Q["gens"]["ours_plane"]
# 表 3 の列: 読めない語の重なり(読み手と条件の組の平均。最下段は撮り直した本物どうし)。label_overlap_summary.py が書き出した results/label_overlap_ratio.json から読む(無ければ列を足さない)
_ov = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "label_overlap_ratio.json")
OV = json.load(open(_ov, encoding="utf-8")) if os.path.exists(_ov) else None
def ovcol(g): return "" if OV is None else (" & " + (f"{OV[g]['overlap']:.2f}" if g in OV else "--"))
def cells_of(fam): return [c for c in CELLS if FAM.get(c, "defocus") == fam]
GENSETS = {"defocus": ["ours_plane", "ours_plane_acc", "ours_plane_fixed", "ours_lampdef", "ours_uni", "albDefocus", "albGauss", "augDepth", "null_band"],
           "lowlight": ["ours_plane", "ours_plane_acc", "ours_grad", "ours_uni", "albBright", "augLight", "null_band"]}
def label(g, fam): return L.get(("L_" + g) if fam == "lowlight" and ("L_" + g) in L else g, g)
MARK = {"通る": "○", "落ちる": "×", "決まらない": "△"}
for k, P in F["per_capture"].items():
    A = F["per_capture_select_by_accuracy"].get(k, {})
    if "gens" in P and "ours_plane" in A.get("gens", {}): P["gens"]["ours_plane_acc"] = A["gens"]["ours_plane"]
# 読み手を使う決まり: 判定に使える撮影が 4 枚以上・文書 5 件以上(文書を単位とするブートストラップと δ に足りる数。本物の撮影の対照で決めた)
MIN_DOCS = 5
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reader_rule import usable, base_usable, mark, NULL_RULE   # 規則 b: その条件で帰無を落とせない読み手は使わない(2026-11-14)
mark(F, extra=(LO,))
def combine(vs):
    vs = [v for v in vs if v]
    if not vs: return None
    return "落ちる" if "落ちる" in vs else ("通る" if all(v == "通る" for v in vs) else "決まらない")
def f2(x): return f"{x:+.2f}"
def f3(x): return f"{x:+.3f}"
# 表 3: 劣化の種類ごとに、生成器ごとの条件(使える読み手をまとめた判定)の数。読み手ごとの数も添える
# 帰無の対照の決まり: 帰無の対照が(使える読み手をまとめて)落ちない条件では、通るを出さない。
# その条件の通るは、生成器も本物の撮影も決まらないにする(落ちるはそのまま)。語を無作為に外すだけの対照を落とせない条件では、通っても語ごとに合う証拠にならないため
def null_failed(c): return combine([F["per_capture"][f"{c}|{rl}"]["gens"]["null_band"]["verdict"] for rl in READERS if usable(F["per_capture"].get(f"{c}|{rl}", {})) and "null_band" in F["per_capture"][f"{c}|{rl}"]["gens"]]) == "落ちる"
NULL_NOT_FAILED = [c for c in CELLS if not null_failed(c)] if NULL_RULE != "b" else []   # 規則 b では使える読み手はみな帰無を落とすので空
for c in NULL_NOT_FAILED:
    for rl in READERS:
        P = F["per_capture"].get(f"{c}|{rl}", {})
        if not usable(P): continue
        for x in [v for g, v in P["gens"].items() if g != "null_band"] + list(P.get("roles", {}).values()):
            if x["verdict"] == "通る": x["verdict"] = "決まらない"
def gated(c): return False   # 帰無が通る条件も上の決まりで扱う(列ごと外すことはしない)
for fam, fn in (("defocus", "auto_tab_verdict.tex"),):   # 低照度は本文に入れない(2026-11-08)
    CC = [c for c in cells_of(fam) if not gated(c)]
    if not CC: continue
    rows = []
    for g in GENSETS[fam]:
        per_cond = [combine([F["per_capture"][f"{c}|{rl}"]["gens"][g]["verdict"] for rl in READERS if usable(F["per_capture"].get(f"{c}|{rl}", {})) and g in F["per_capture"][f"{c}|{rl}"]["gens"]]) for c in CC]
        per_cond = [v for v in per_cond if v]
        per_reader = []
        for rl in READERS:
            vs = [F["per_capture"][f"{c}|{rl}"]["gens"][g]["verdict"] for c in CC if base_usable(F["per_capture"].get(f"{c}|{rl}", {})) and g in F["per_capture"][f"{c}|{rl}"]["gens"]]
            per_reader.append(f"{vs.count('通る')}/{vs.count('決まらない')}/{vs.count('落ちる')}")
        rows.append(f"{label(g, fam)} & " + " & ".join(str(per_cond.count(v)) for v in ("通る", "決まらない", "落ちる")) + " & " + " & ".join(per_reader) + ovcol(g) + r" \\")
    roles_cond = []; roles_reader = {rl: [] for rl in READERS}
    for c in CC:
        R = {}
        for rl in READERS:
            P = F["per_capture"].get(f"{c}|{rl}", {})
            if not base_usable(P): continue
            for ro, x in P.get("roles", {}).items():
                roles_reader[rl].append(x["verdict"])
                if usable(P): R.setdefault(ro, []).append(x["verdict"])
        roles_cond += [combine(v) for v in R.values()]
    rows.append(r"\midrule")
    rows.append(f"{L['roles']} & " + " & ".join(str(roles_cond.count(v)) for v in ("通る", "決まらない", "落ちる")) + " & " +
                " & ".join(f"{roles_reader[rl].count('通る')}/{roles_reader[rl].count('決まらない')}/{roles_reader[rl].count('落ちる')}" for rl in READERS) + ovcol("roles") + r" \\")
    open(f"{OUTD}/{fn}", "w", encoding="utf-8").write("\n".join(rows) + "\n")
# 表 2: 正答率の差(測る語での差の絶対値の平均)を、読み手ごとに条件をまたいで平均する
rows = []; ALLP = []
# 本物との語ごとの一致(κ)の平均も並べる: 撮り直し(同じ組の残りの撮影との κ)・帯で選ぶ・誤り率で選ぶ・帰無の対照。誤り率では完璧な帰無の対照と比べるため
def krow(Ps): return [st.mean(P["ceiling"]["mean"] for P in Ps)] + [st.mean(P["gens"][g]["kappa"]["mean"] for P in Ps) for g in ("ours_plane", "ours_plane_acc", "null_band")]
for rl in READERS:
    Ps = [F["per_capture"][f"{c}|{rl}"] for c in cells_of("defocus") if not gated(c) and usable(F["per_capture"].get(f"{c}|{rl}", {}))]
    if not Ps: continue
    ALLP += Ps; n = sum(P["n_captures"] for P in Ps)
    vals = [st.mean(P["gens"][g]["abs_dacc"] for P in Ps) for g in ("ours_plane_acc", "ours_plane", "ours_uni")]
    rows.append(f"{rl} & {len(Ps)} & {n} & " + " & ".join(f"{v:.3f}" for v in vals) + " & " + " & ".join(f"{v:.2f}" for v in krow(Ps)) + r" \\")
vals = [st.mean(P["gens"][g]["abs_dacc"] for P in ALLP) for g in ("ours_plane_acc", "ours_plane", "ours_uni")]
rows.append(r"\midrule")
rows.append(f"{L['all']} & {len(ALLP)} & {sum(P['n_captures'] for P in ALLP)} & " + " & ".join(f"{v:.3f}" for v in vals) + " & " + " & ".join(f"{v:.2f}" for v in krow(ALLP)) + r" \\")
print("表 2 の全体の κ(撮り直し・帯・誤り率・帰無):", [round(v, 3) for v in krow(ALLP)], "ライブラリ等の κ:", {g: round(st.mean(P["gens"][g]["kappa"]["mean"] for P in ALLP), 3) for g in ("ours_uni", "albDefocus", "albGauss", "augDepth")},
      "誤り率>帰無:", sum(F["per_capture_select_by_accuracy"][k]["gens"]["ours_plane"]["kappa"]["mean"] > F["per_capture"][k]["gens"]["null_band"]["kappa"]["mean"] for k in F["per_capture"] if F["per_capture"][k] in ALLP), "/", len(ALLP))
open(f"{OUTD}/auto_tab_exp1.tex", "w", encoding="utf-8").write("\n".join(rows) + "\n")
# 付録: 設定を一つに固める(確かめる文書を除いた残りの文書で一つ選ぶ。results/facts_lodo.json、run_lodo.py)
rows = []
for c in cells_of("defocus"):   # 条件ごとに一行: 読み手ごとの判定の印(Tesseract・docTR・Vision・Mistral の順、使えない読み手は ·)と、まとめた判定
    if gated(c): continue
    fx = []; pi = []
    for rl in READERS:
        P = F["per_capture"].get(f"{c}|{rl}", {}); Q = LO.get(f"{c}|{rl}", {})
        ok = usable(P) and "ours_plane" in Q.get("gens", {})
        fx.append(Q["gens"]["ours_plane"]["verdict"] if ok else None); pi.append(P["gens"]["ours_plane"]["verdict"] if ok else None)
    mk = lambda vs: "".join(MARK[v] if v else "·" for v in vs)
    rows.append(f"{c} & {mk(fx)} & {MARK.get(combine(fx), '·')} & {mk(pi)} & {MARK.get(combine(pi), '·')}" + r" \\")
open(f"{OUTD}/auto_tab_xdoc.tex", "w", encoding="utf-8").write("\n".join(rows) + "\n")
# 本文で引く数: 生成器と選び方の組み合わせ(帰無を除く)・本物の撮影・読み手で判定が割れた組み合わせ
CD = cells_of("defocus"); GG = [g for g in GENSETS["defocus"] if g != "null_band"]
def cv(c, g): return combine([F["per_capture"][f"{c}|{rl}"]["gens"][g]["verdict"] for rl in READERS if usable(F["per_capture"].get(f"{c}|{rl}", {})) and g in F["per_capture"][f"{c}|{rl}"]["gens"]])
gv = [v for v in (cv(c, g) for c in CD for g in GG) if v]
rv = []
for c in CD:
    R_ = {}
    for rl in READERS:
        P = F["per_capture"].get(f"{c}|{rl}", {})
        if usable(P):
            for ro, x in P.get("roles", {}).items(): R_.setdefault(ro, []).append(x["verdict"])
    rv += [combine(v) for v in R_.values()]
sp = []
for c in CD:
    for g in GG + ["null_band"]:
        vs = {rl: F["per_capture"][f"{c}|{rl}"]["gens"][g]["verdict"] for rl in READERS if usable(F["per_capture"].get(f"{c}|{rl}", {})) and g in F["per_capture"][f"{c}|{rl}"]["gens"]}
        if vs and "通る" in vs.values() and "落ちる" in vs.values(): sp.append((c, g, [rl for rl, v in vs.items() if v == "落ちる"]))
t = lambda vs: "/".join(str(vs.count(v)) for v in ("通る", "決まらない", "落ちる"))
print(f"帰無が落ちない条件: {NULL_NOT_FAILED}")
print("規則:", NULL_RULE, " 使える(条件, 読み手):", {rl: sum(usable(F['per_capture'].get(f'{c}|{rl}', {})) for c in CD) for rl in READERS}, " 文書が足りる:", {rl: sum(base_usable(F['per_capture'].get(f'{c}|{rl}', {})) for c in CD) for rl in READERS})
print("使える読み手が一人もいない条件:", [c for c in CD if not any(usable(F['per_capture'].get(f'{c}|{rl}', {})) for rl in READERS)])
print(f"生成器と選び方 {len(gv)} 通り(通る/決まらない/落ちる): {t(gv)}  本物の撮影 {len(rv)} 通り: {t(rv)}")
print(f"読み手で割れた組み合わせ: {len(sp)}(Tesseract が落とす {sum('Tesseract' in f for _, _, f in sp)})  {sp}")
print("ok")

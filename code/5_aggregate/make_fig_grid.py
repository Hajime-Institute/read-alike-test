# -*- coding: utf-8 -*-
"""図 3: 生成器 × 条件の判定の格子（色を使わない版、2026-11-14）。
判定は使える読み手をまとめたもの。使える読み手は reader_rule.py の決まり（規則 b: 文書 5 件以上で、その条件で帰無の対照を落とせること）。
セル: 落ちる＝黒地に ✗、決まらない＝薄い灰、通る＝白地に ✓。比べていない組み合わせは空ける。使える読み手がいない条件は列ごと斜線。
見出しの下に、その条件で使えた読み手（T＝Tesseract、D＝docTR、V＝Vision、M＝Mistral）。最下段は本物の撮影を生成器の代わりにしたときの、通った数／取り出した撮影の数。
その下に、使えた読み手での基準（本物どうしの κ）の平均と δ の平均。
使い方: python make_fig_grid.py <facts_defocus.json> <出力 pdf>"""
import sys, os, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reader_rule import usable, mark
F = json.load(open(sys.argv[1], encoding="utf-8")); OUT = sys.argv[2]
CELLS = [c for c in F["cells"] if F.get("family", {}).get(c, "defocus") == "defocus"]; READERS = F["readers"]
GENS = [("ours_plane", "Tilted-page defocus"), ("ours_plane_acc", "Tilted-page (accuracy-based)"), ("ours_plane_fixed", "Tilted-page (set on other documents)"),
        ("ours_lampdef", "Tilted-page + desk lamp"), ("ours_uni", "Uniform disk blur"), ("albDefocus", "albumentations Defocus"),
        ("albGauss", "albumentations GaussianBlur"), ("augDepth", "Augraphy DepthSimulatedBlur")]
LO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "facts_lodo.json"), encoding="utf-8"))
for k, P in F["per_capture"].items():
    A = F["per_capture_select_by_accuracy"].get(k, {}); Q = LO.get(k, {})
    if "gens" in P and "ours_plane" in A.get("gens", {}): P["gens"]["ours_plane_acc"] = A["gens"]["ours_plane"]
    if "gens" in P and "ours_plane" in Q.get("gens", {}): P["gens"]["ours_plane_fixed"] = Q["gens"]["ours_plane"]
mark(F, extra=(LO,))
def combine(vs):
    vs = [v for v in vs if v]
    if not vs: return None
    return "落ちる" if "落ちる" in vs else ("通る" if all(v == "通る" for v in vs) else "決まらない")
FACE = {"通る": "white", "決まらない": "0.82", "落ちる": "0.12"}
GLYPH = {"通る": ("✓", "black"), "決まらない": ("", "black"), "落ちる": ("✗", "white")}
INI = {"Tesseract": "T", "docTR": "D", "Vision": "V", "Mistral": "M"}
nr = len(GENS) + 1; nc = len(CELLS)
fig = plt.figure(figsize=(7.0, 3.0))
ax = fig.add_axes([0.32, 0.02, 0.67, 0.96])
for c, cell in enumerate(CELLS):
    Ps = {rl: F["per_capture"].get(f"{cell}|{rl}", {}) for rl in READERS}
    U = [rl for rl in READERS if usable(Ps[rl])]
    if not U:   # 使える読み手がいない条件: 列ごと斜線
        ax.add_patch(Rectangle((c, 0), 0.92, nr - 0.08, fc="white", ec="0.55", lw=0.4, hatch="////", zorder=1))
        ax.text(c + 0.46, nr / 2, "no qualified reader", rotation=90, ha="center", va="center", fontsize=6.5, color="0.15", bbox=dict(fc="white", ec="none", pad=1.2), zorder=3)
    for r, (g, gl) in enumerate(GENS):
        y = nr - 1 - r
        if not U: continue
        v = combine([Ps[rl]["gens"][g]["verdict"] for rl in U if g in Ps[rl]["gens"]])
        if v is None: continue   # 比べていない組み合わせ(卓上灯つきは L3 だけ)
        ax.add_patch(Rectangle((c, y), 0.92, 0.92, fc=FACE[v], ec="0.45", lw=0.4))
        s, col = GLYPH[v]
        if s: ax.text(c + 0.46, y + 0.44, s, ha="center", va="center", fontsize=9, color=col, fontweight="bold")
    # 本物の撮影の行: 取り出した撮影ごとに、使えた読み手をまとめた判定
    if U:
        R = {}
        for rl in U:
            for ro, x in Ps[rl].get("roles", {}).items(): R.setdefault(ro, []).append(x["verdict"])
        vv = [combine(v) for v in R.values()]
        ax.add_patch(Rectangle((c, 0), 0.92, 0.92, fc="white", ec="0.45", lw=0.4))
        ax.text(c + 0.46, 0.46, f"{vv.count('通る')}/{len(vv)}" + (f"\n✗{vv.count('落ちる')}" if vv.count("落ちる") else ""), ha="center", va="center", fontsize=7)
        ref = sum(Ps[rl]["ceiling"]["mean"] for rl in U) / len(U); dl = sum(Ps[rl]["delta"] for rl in U) / len(U)
        ax.text(c + 0.46, -0.45, f"{ref:.2f}", ha="center", va="center", fontsize=6.5)
        ax.text(c + 0.46, -0.95, f"{dl:.2f}", ha="center", va="center", fontsize=6.5)
    else:
        for yy in (-0.45, -0.95): ax.text(c + 0.46, yy, "–", ha="center", va="center", fontsize=6.5, color="0.4")
    # 見出し: 機種と焦点の段階・照明・使えた読み手
    ax.text(c + 0.46, nr + 0.05, cell.rsplit(" ", 1)[1], ha="center", va="bottom", fontsize=7)
    ax.text(c + 0.46, nr - 0.02, "".join(INI[rl] for rl in U) if U else "none", ha="center", va="top", fontsize=6, color="0.25", style="italic") if False else None
ax.set_xlim(-0.05, nc); ax.set_ylim(-2.05, nr + 1.55); ax.axis("off")
# 凡例
LEG = [("通る", "pass"), ("決まらない", "undecided"), ("落ちる", "fail")]
x0 = 0.0
for v, name in LEG:
    ax.add_patch(Rectangle((x0, -1.75), 0.42, 0.42, fc=FACE[v], ec="0.45", lw=0.4)); s, col = GLYPH[v]
    if s: ax.text(x0 + 0.21, -1.55, s, ha="center", va="center", fontsize=6.5, color=col, fontweight="bold")
    ax.text(x0 + 0.55, -1.55, name, ha="left", va="center", fontsize=6.8); x0 += 2.0
ax.add_patch(Rectangle((x0, -1.75), 0.42, 0.42, fc="white", ec="0.55", lw=0.4, hatch="////")); ax.text(x0 + 0.55, -1.55, "no reader stops the null baseline", ha="left", va="center", fontsize=6.8)
# 使えた読み手の行(見出しの直下に一段)
for c, cell in enumerate(CELLS):
    U = [rl for rl in READERS if usable(F["per_capture"].get(f"{cell}|{rl}", {}))]
    ax.text(c + 0.46, nr + 0.0 - 0.0, "", fontsize=1)
    ax.text(c + 0.46, nr + 0.55, "".join(INI[rl] for rl in U) if U else "–", ha="center", va="bottom", fontsize=6.5, color="0.2")
for c, cell in enumerate(CELLS): pass
for r, (g, gl) in enumerate(GENS): ax.text(-0.15, nr - 1 - r + 0.46, gl, ha="right", va="center", fontsize=7.5)
ax.text(-0.15, 0.46, "Real captures (passed / taken out)", ha="right", va="center", fontsize=7.5)
ax.text(-0.15, -0.45, "Mean reference $\\kappa$", ha="right", va="center", fontsize=7)
ax.text(-0.15, -0.95, "Mean $\\delta$", ha="right", va="center", fontsize=7)
ax.text(-0.15, nr + 0.62, "Qualified readers (T: Tesseract, D: docTR)", ha="right", va="bottom", fontsize=7)
ax.text(-0.15, nr + 0.08, "Lighting", ha="right", va="bottom", fontsize=7)
groups = []
for c, cell in enumerate(CELLS):
    head = cell.rsplit(" ", 1)[0]
    if groups and groups[-1][0] == head: groups[-1][2] = c
    else: groups.append([head, c, c])
for head, c0, c1 in groups:
    ax.text((c0 + c1) / 2 + 0.46, nr + 1.12, head, ha="center", va="bottom", fontsize=7.5)
    ax.plot([c0 + 0.05, c1 + 0.87], [nr + 1.07, nr + 1.07], color="0.3", lw=0.5, clip_on=False)
ax.plot([0, nc - 0.08], [-0.15, -0.15], color="0.6", lw=0.4)
fig.savefig(OUT); fig.savefig(OUT.replace(".pdf", ".png"), dpi=220)
print("ok")

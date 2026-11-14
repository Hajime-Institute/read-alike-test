# -*- coding: utf-8 -*-
"""合成の劣化で「読めない語」の正解を作ったとき、その正解が本物の撮影でどれだけ成り立つかをまとめる。
audit_angles.py を LABEL_OUT つきで回した出力(検査画像ごとに、本物で読めない語の数・出どころで読めない語の数・両方で読めない語の数)を読む。
出どころは、撮り直したもう一枚の本物(上限)・各生成器(帯で選ぶ prof / 誤り率で選ぶ acc)・帰無の対照。
数えるのは、読めない語の重なり(両方で読めない語の数を、本物と出どころで読めない語の数の平均で割る。Dice)。出どころがほとんど語を落とさないときも決まる。
あわせて、出どころで読めない語のうち本物でも読めない割合(適合)と、本物で読めない語のうち出どころでも読めない割合(再現)も出す。
検査画像ごとに出して平均し、読み手と条件の組み合わせごとにまとめる。読み手を使う決まりは本文と同じ(検査画像が文書 5 件以上・4 枚以上)。
使い方: python -I label_overlap_summary.py <labout のディレクトリ> [facts_defocus.json] [固定の設定の labout のディレクトリ] [比を書き出す json]
表 3 の列(読めない語の重なり、撮り直し＝1)は、最後の引数の json から write_tables.py が読む。"""
import sys, os, json, glob, collections, statistics as st
D = sys.argv[1]; FACTS = sys.argv[2] if len(sys.argv) > 2 else None
DLODO = sys.argv[3] if len(sys.argv) > 3 else None; OUTJ = sys.argv[4] if len(sys.argv) > 4 else None
CELL = {("WP", "Ob820"): "Nokia 1", ("WP", "Ob940"): "Nokia 2", ("Android", "Ob1"): "Samsung 1", ("Android", "Ob2"): "Samsung 2"}
RD = {"tessblk": "Tesseract", "doctrblk": "docTR", "visionblk": "Vision", "vlmblk": "Mistral"}
# (条件, 読み手, 出どころ) → 検査画像 → [本物で読めない, 出どころで読めない, 両方]
acc = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0, 0.0]))
files = [(f, "") for f in glob.glob(os.path.join(D, "*.jsonl"))] + ([(f, "lodo") for f in glob.glob(os.path.join(DLODO, "*.jsonl"))] if DLODO else [])
for f, tag in files:
    for l in open(f):
        r = json.loads(l)
        if tag == "lodo":   # 設定を一つに固定した回は、傾いた紙のぼけの行だけを使う
            if r["src"] != "ours_plane": continue
            r = dict(r, src="ours_plane_fixed")
        cell = f"{CELL[(r['ph'], r['ob'])]} {r['light']}"; rd = RD[r["reader"]]
        if r["src"] in ("recapture", "null_band"):
            if r["sel"] != "prof": continue   # 撮り直しと帰無は選び方によらない(prof の回の分だけ使う)
            src = r["src"]
        else:
            src = f"{r['src']}|{r['sel']}"
        a = acc[(cell, rd, src)][(r["d"], r["ang"])]
        a[0] += r["real_missed"]; a[1] += r["src_missed"]; a[2] += r["both"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reader_rule import NULL_RULE   # 規則 b(2026-11-14): その条件で帰無を落とせない読み手は使わない(帰無の判定は FACTS から)
_NULLV = {}
if FACTS and NULL_RULE == "b":
    _F0 = json.load(open(FACTS, encoding="utf-8"))
    _NULLV = {k: P.get("gens", {}).get("null_band", {}).get("verdict") for k, P in _F0["per_capture"].items()}
def usable(cell, rd):
    imgs = acc.get((cell, rd, "recapture"), {})
    if _NULLV and _NULLV.get(f"{cell}|{rd}") != "落ちる": return False
    return len(imgs) >= 4 and len({d for d, _ in imgs}) >= 5
def scores(imgs):
    P = [b / s for rm, s, b in imgs.values() if s > 0]; R = [b / rm for rm, s, b in imgs.values() if rm > 0]
    Dc = [2 * b / (rm + s) for rm, s, b in imgs.values() if rm + s > 0]
    return (st.mean(P) if P else float("nan"), st.mean(R) if R else float("nan"), st.mean(Dc))
SRC = [("recapture", "撮り直したもう一枚の本物"), ("ours_plane|prof", "傾いた紙のぼけ(帯で選ぶ)"), ("ours_plane|acc", "傾いた紙のぼけ(誤り率で選ぶ)"),
       ("ours_plane_fixed|prof", "傾いた紙のぼけ(設定を一つに固定)"), ("ours_lampdef|prof", "傾いた紙のぼけ＋卓上灯(帯)"), ("null_band", "帰無の対照"), ("ours_uni|prof", "一様な円のぼけ(帯)"),
       ("albDefocus|prof", "albumentations Defocus(帯)"), ("albGauss|prof", "albumentations GaussianBlur(帯)"), ("augDepth|prof", "Augraphy DepthSimulatedBlur(帯)")]
pairs = sorted({(c, rd) for c, rd, _ in acc if usable(c, rd)})
print(f"使える読み手×条件: {len(pairs)}")
print(f"{'出どころ':34s} {'組':>3s} {'重なり':>6s} {'撮り直し比':>8s} {'適合':>6s} {'再現':>6s}")
table = {}; RATIO = {}
for key, name in SRC:
    ps = []; rs = []; ds = []; rat = []
    for c, rd in pairs:
        imgs = acc.get((c, rd, key))
        if not imgs: continue
        p, r, dc = scores(imgs); ps.append(p); rs.append(r); ds.append(dc)
        rat.append(dc / scores(acc[(c, rd, "recapture")])[2])
    if not ds: continue
    table[key] = ds
    m = lambda v: st.mean([x for x in v if x == x]) if any(x == x for x in v) else float("nan")
    print(f"{name:34s} {len(ds):3d} {st.mean(ds):6.2f} {st.mean(rat):8.2f} {m(ps):6.2f} {m(rs):6.2f}")
    RATIO[key] = {"overlap": st.mean(ds), "ratio": st.mean(rat), "n": len(ds)}
# 判定ごと(facts の読み手ごとの判定)。帯で選んだ生成器の行だけ。表 3 の読み手ごとの数と同じ基準にそろえる(2026-11-14):
# 帰無の対照の行は入れず、読み手をまとめた帰無が落ちない条件では、読み手ごとの通るを決まらないに下げる(write_tables.py と同じ)。
# 11-13 までの本文の 1.13・0.46 は、帰無の決まりを当てる前で帰無の行も入れた値だった(通る 44 通り)。この基準では 1.15・0.43(通る 21 通り)。
def _combine(vs):
    vs = [v for v in vs if v]
    return None if not vs else ("落ちる" if "落ちる" in vs else ("通る" if all(v == "通る" for v in vs) else "決まらない"))
if FACTS:
    F = json.load(open(FACTS, encoding="utf-8")); byv = collections.defaultdict(list)
    nullc = {c: _combine([F["per_capture"][f"{c}|{rd}"]["gens"].get("null_band", {}).get("verdict") for cc, rd in pairs if cc == c]) for c, _ in pairs}
    for c, rd in pairs:
        P = F["per_capture"].get(f"{c}|{rd}", {})
        for g, x in P.get("gens", {}).items():
            if g == "null_band": continue
            imgs = acc.get((c, rd, f"{g}|prof"))
            b = acc.get((c, rd, "recapture"))
            v = "決まらない" if (nullc[c] != "落ちる" and x["verdict"] == "通る") else x["verdict"]
            if imgs and b: byv[v].append(scores(imgs)[2] / scores(b)[2])
    print("\n読み手ごとの判定(表 3 と同じ基準: 帰無の決まりを当て、帰無の行は除く)ごとの、撮り直しに対する重なりの比")
    for v in ("通る", "決まらない", "落ちる"):
        if byv[v]: print(f"  {v:6s} {st.mean(byv[v]):5.2f}  (組 {len(byv[v])})")
# 表 3 の列: 生成器の行の名前(write_tables.py の GENSETS)ごとの、撮り直しに対する重なりの比
if OUTJ:
    KEY = {"ours_plane": "ours_plane|prof", "ours_plane_acc": "ours_plane|acc", "ours_plane_fixed": "ours_plane_fixed|prof", "ours_lampdef": "ours_lampdef|prof",
           "ours_uni": "ours_uni|prof", "albDefocus": "albDefocus|prof", "albGauss": "albGauss|prof", "augDepth": "augDepth|prof", "null_band": "null_band", "roles": "recapture"}
    json.dump({k: RATIO[v] for k, v in KEY.items() if v in RATIO}, open(OUTJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", OUTJ)

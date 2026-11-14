# -*- coding: utf-8 -*-
"""校正(半分の文書)で合成の設定を選び、残り半分で評価する。
- 文書 = ページ ID の先頭 4 桁(8752_001 と 8752_003 は同じ手紙)。校正/評価の分割と bootstrap は文書単位
- 分割: split.py(文書 ID を seed 1 で並べ替え、前半を校正、後半を評価)。標本は common.sample_pages(set, npages)
- 選び方: 地域プロファイルだけ。各ページの正解単語列を連続 5 区間に分け、区間ごとの単語正答率(全単語)を
  実 2B と合成で比べ、校正ページ全体で差の二乗和が最小の格子点を選ぶ。kappa は選択に使わない
- 評価: 正答率の差(合成 - 実 2B、評価ページ全単語のミクロ平均)、
  kappa(実 2B と合成の 読めた/読めない、4B で読めた単語だけ、評価ページを連結して 1 つの kappa)
- 参照: kappa(3B, 3A)を同じマスクで。300 dpi の固定しきい値と適応しきい値という別の取り込み経路で、反復撮影ではない
使い方: python -I analyze.py <set> <npages> [nboot]  (npages は ocr_run.py と同じ標本の大きさ)"""
import sys, os, json, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from score_words import read_vector
from ocr_run import SIGMAS, THRS, cond_name

tset = sys.argv[1]
NPAGES = int(sys.argv[2])
NB = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
GRID = [cond_name(s, t) for s in SIGMAS for t in THRS]
NAIVE = cond_name(0.0, 128)
REAL = ["2B", "4B", "3B", "3A"]
CONDS = REAL + GRID
from split import split_pages, doc

recs = {}
for c in CONDS:
    p = os.path.join(RES, f"ocr_{tset}_{c}.jsonl")
    recs[c] = {r["page"]: r for r in read_jsonl(p)} if os.path.exists(p) else {}
sample = [p for p, _ in sample_pages(tset, NPAGES)]
cal, ev = split_pages(sample)
V, NW = {}, {}  # page -> cond -> np.array ok
for p in sample:
    if p not in recs["2B"] or p not in recs["4B"]: continue
    gt = read_gt(paths(tset, "2B", p, recs["2B"][p]["sub"])[2])
    V[p] = {}
    for c in CONDS:
        if p in recs[c]:
            g, ok = read_vector(gt, recs[c][p]["text"])
            V[p][c] = np.array(ok, dtype=np.int8)
    NW[p] = len(g)
missing = [p for p in sample if p not in V]
assert not missing, f"2B/4B missing: {missing[:5]}"
cal = [p for p in cal if NW[p] > 0]; ev = [p for p in ev if NW[p] > 0]
pages = cal + ev
docs = sorted({doc(p) for p in pages})
cal_docs = {doc(p) for p in cal}; ev_docs = {doc(p) for p in ev}
have_all = lambda c, pp: all(c in V[p] for p in pp)
for c in GRID: assert have_all(c, cal), f"grid {c} missing on calibration pages"
have = [c for c in CONDS if have_all(c, ev)]


def profile(v, k=5):
    return np.array([b.mean() if len(b) else np.nan for b in np.array_split(v, k)])


def kappa(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) == 0: return float("nan")
    po = (a == b).mean(); pa, pb = a.mean(), b.mean()
    pe = pa * pb + (1 - pa) * (1 - pb)
    return float("nan") if pe >= 1 else float((po - pe) / (1 - pe))


def stats(pp, c, ref="2B"):
    """評価ページ群 pp での指標。pp は重複を許す(bootstrap 用)"""
    a_all = np.concatenate([V[p][c] for p in pp]); r_all = np.concatenate([V[p][ref] for p in pp])
    m = np.concatenate([V[p]["4B"] for p in pp]).astype(bool)
    return {"acc": float(a_all.mean()), "acc_ref": float(r_all.mean()), "diff": float(a_all.mean() - r_all.mean()),
            "macc": float(a_all[m].mean()), "macc_ref": float(r_all[m].mean()),
            "kappa": kappa(r_all[m], a_all[m]), "n_mask": int(m.sum()),
            "fail_ref_mask": int((1 - r_all[m]).sum()), "fail_c_mask": int((1 - a_all[m]).sum()),
            "both_fail_mask": int(((1 - r_all[m]) * (1 - a_all[m])).sum())}


def boot(pp, fn, nb=NB, seed=0):
    by = {}
    for p in pp: by.setdefault(doc(p), []).append(p)
    ds = sorted(by); rng = np.random.default_rng(seed); out = []
    for _ in range(nb):
        smp = [p for d in rng.choice(ds, len(ds), replace=True) for p in by[d]]
        out.append(fn(smp))
    out = np.array(out, float)
    return [float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))]


# 校正: 地域プロファイルの二乗和
loss = {}
for c in GRID:
    loss[c] = float(np.nansum([(profile(V[p][c]) - profile(V[p]["2B"])) ** 2 for p in cal]))
chosen = min(loss, key=loss.get)
if not (have_all(chosen, ev) and have_all(NAIVE, ev)):
    # 校正だけ済んだ段階。選んだ設定を評価ページで読んでから再実行する
    print("calibration loss:", {c: round(v, 4) for c, v in sorted(loss.items(), key=lambda x: x[1])})
    print("CHOSEN", chosen, "-> run it (and naive) on the evaluation pages, then rerun")
    sys.exit(2)

res = {"set": tset, "n_pages": len(pages), "n_docs": len(docs), "cal_pages": cal, "eval_pages": ev,
       "n_cal_docs": len(cal_docs), "n_eval_docs": len(ev_docs),
       "cal_loss": loss, "chosen": chosen, "naive": NAIVE,
       "words_eval": int(sum(NW[p] for p in ev)), "words_cal": int(sum(NW[p] for p in cal))}

# 評価
res["eval"] = {}
for c in ["4B", chosen, NAIVE] + [g for g in GRID if g in have]:
    if c in res["eval"]: continue
    res["eval"][c] = stats(ev, c)
for c, tag in [(chosen, "chosen"), (NAIVE, "naive")]:
    res[f"ci_{tag}"] = {"kappa": boot(ev, lambda s: stats(s, c)["kappa"]),
                        "diff": boot(ev, lambda s: stats(s, c)["diff"])}
res["ci_kappa_chosen_minus_naive"] = boot(ev, lambda s: stats(s, chosen)["kappa"] - stats(s, NAIVE)["kappa"])
if "3B" in have and "3A" in have:
    res["ref_3B_3A_eval"] = stats(ev, "3A", ref="3B")
    res["ref_3B_3A_eval"]["ci_kappa"] = boot(ev, lambda s: stats(s, "3A", ref="3B")["kappa"])
    res["ref_3B_3A_all"] = stats(pages, "3A", ref="3B")  # 校正ページも含む(格子と無関係なので循環しない)
    res["ref_3B_3A_all"]["ci_kappa"] = boot(pages, lambda s: stats(s, "3A", ref="3B")["kappa"])
    res["ref_2B_3B_eval"] = stats(ev, "3B", ref="2B")
    res["ref_2B_3B_eval"]["ci_kappa"] = boot(ev, lambda s: stats(s, "3B", ref="2B")["kappa"])
# 各条件の正答率の範囲(ページ単位)
res["page_acc"] = {c: {p: float(V[p][c].mean()) for p in pages if c in V[p]} for c in CONDS}
res["range_eval"] = {c: [float(min(V[p][c].mean() for p in ev)), float(max(V[p][c].mean() for p in ev))] for c in have}
res["micro_all"] = {c: float(np.concatenate([V[p][c] for p in pages]).mean()) for c in REAL if have_all(c, pages)}

out = os.path.join(RES, f"summary_{tset}.json")
with open(out, "w") as f: json.dump(res, f, indent=1)

# 表示
print(f"{tset}: pages {len(pages)} (docs {len(docs)}), cal {len(cal)} pages / {len(cal_docs)} docs, eval {len(ev)} pages / {len(ev_docs)} docs, eval words {res['words_eval']}")
print("micro acc (all pages):", {c: round(v, 4) for c, v in res["micro_all"].items() if not c.startswith("syn")})
print("calibration loss (lower = closer regional profile):")
for c in sorted(loss, key=loss.get): print(f"  {c:16s} {loss[c]:.4f}")
print("chosen:", chosen)
print("eval (ref = real 2B, mask = words read right on 4B):")
print(f"  {'cond':16s} {'acc':>6s} {'acc2B':>6s} {'diff':>7s} {'kappa':>6s} {'fail2B':>6s} {'failC':>6s} {'both':>5s} {'nmask':>6s}")
for c, s in res["eval"].items():
    tag = " <- chosen" if c == chosen else (" <- naive" if c == NAIVE else "")
    print(f"  {c:16s} {s['acc']:6.3f} {s['acc_ref']:6.3f} {s['diff']:+7.3f} {s['kappa']:6.3f} {s['fail_ref_mask']:6d} {s['fail_c_mask']:6d} {s['both_fail_mask']:5d} {s['n_mask']:6d}{tag}")
print("CI chosen:", res["ci_chosen"], " CI naive:", res["ci_naive"], " CI kappa chosen-naive:", res["ci_kappa_chosen_minus_naive"])
for k in ["ref_3B_3A_eval", "ref_3B_3A_all", "ref_2B_3B_eval"]:
    if k in res:
        s = res[k]; print(f"{k}: kappa {s['kappa']:.3f} CI {s['ci_kappa']}  acc {s['acc_ref']:.3f}/{s['acc']:.3f}  fail {s['fail_ref_mask']}/{s['fail_c_mask']} both {s['both_fail_mask']} nmask {s['n_mask']}")
print("wrote", out)

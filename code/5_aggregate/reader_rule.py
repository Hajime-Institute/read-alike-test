# -*- coding: utf-8 -*-
"""読み手を使う決まり（集計のスクリプトで共通）。2026-11-14 から規則 b（本人了承）。
使える読み手: その条件で判定に使える撮影が 4 枚以上・文書 5 件以上で、かつ、その条件でその読み手が帰無の対照を落とせること。
帰無の対照（帯ごとの正答率どおりに語を無作為に落とす）を落とせない読み手の「通る」は、語ごとに合う証拠にならないため。
NULL_RULE=combined で 11-13 までの決まり（読み手をまとめた帰無が落ちない条件では通るを決まらないにする）に戻せる。"""
import os
NULL_RULE = os.environ.get("NULL_RULE", "b")
def base_usable(P): return "gens" in P and P.get("n_captures", 0) >= 4 and P.get("n_docs", 0) >= 5
def null_stopped(P): return P.get("gens", {}).get("null_band", {}).get("verdict") == "落ちる"
def usable_self(P):
    """帰無の判定を自分で持つ記録（per_capture・known_fidelity・二つ目の文書セット）に使う"""
    return base_usable(P) and (NULL_RULE != "b" or null_stopped(P))
def mark(F, sections=("per_capture_select_by_accuracy", "cross_document", "per_capture_docs_6_10", "lodo"), extra=()):
    """規則 b: per_capture で帰無を落とせない（条件|読み手）に印 null_not_stopped を付け、同じ key の他の節（extra の dict も）に写す"""
    if NULL_RULE != "b": return set()
    bad = {k for k, P in F["per_capture"].items() if not null_stopped(P)}
    for D in [F["per_capture"]] + [F.get(s, {}) for s in sections] + list(extra):
        for k in bad:
            if isinstance(D.get(k), dict): D[k]["null_not_stopped"] = True
    return bad
def usable(P): return base_usable(P) and not P.get("null_not_stopped")

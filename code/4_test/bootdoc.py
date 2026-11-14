# -*- coding: utf-8 -*-
"""文書を単位とするブートストラップ。同じ文書の撮影どうし・対どうしは似るので、文書をまとめて引き直す。
入力は (文書, 値) の並び。文書を重複を許して引き、引いた文書の値をすべて平均する。"""
import random, statistics as st
def boot_doc(gv, n=2000, seed=0):
    G={}
    for g,v in gv:
        if v==v: G.setdefault(g,[]).append(v)
    keys=sorted(G)
    if len(keys)<2: return float("nan"),float("nan")
    rnd=random.Random(seed); ms=[]
    for _ in range(n):
        s=[x for k in (rnd.choice(keys) for _ in keys) for x in G[k]]; ms.append(st.mean(s))
    ms.sort(); return ms[int(.025*n)],ms[int(.975*n)]
def ndocs(gv): return len({g for g,v in gv if v==v})

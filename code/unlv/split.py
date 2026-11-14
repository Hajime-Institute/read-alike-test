# -*- coding: utf-8 -*-
"""校正/評価の分割(文書単位)。文書 = ページ ID の先頭 4 桁。
文書 ID を整列して seed 1 で並べ替え、前半を校正、後半を評価にする。
OCR の前に決まる(読んだ結果を見ずに決まる)。"""
import random


def doc(p):
    return p.split("_")[0]


def split_pages(pages):
    docs = sorted({doc(p) for p in pages})
    rnd = random.Random(1); rnd.shuffle(docs)
    cal_docs = set(docs[: len(docs) // 2])
    cal = [p for p in pages if doc(p) in cal_docs]
    ev = [p for p in pages if doc(p) not in cal_docs]
    return cal, ev

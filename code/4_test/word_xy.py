# -*- coding: utf-8 -*-
"""正解の単語ごとの、ページの上のおおよその位置(縦・横の比)。正解の文字は元の文書の行の並びのままなので、
縦は行の番号の比、横は行の中の何語目かの比で近似する。並びは score_words.words と同じ単語に対応する。"""
from score_words import words
def word_xy(gt_text):
    lines=[l for l in gt_text.replace("﻿","").splitlines()]
    xy=[]; nl=max(1,len(lines))
    for li,l in enumerate(lines):
        ws=words(l)
        for wi,_ in enumerate(ws): xy.append(((wi+0.5)/len(ws), (li+0.5)/nl))
    return xy

# -*- coding: utf-8 -*-
"""書き写しを正解と単語単位で照らす。正解の各単語が「読めた(1) / 読めなかった(0)」のベクトルを作る。
正規化: NFKC(合字 ﬁ→fi)、BOM 除去、小文字化、単語の前後の句読点を外す。対応は difflib の一致ブロック。"""
import re, unicodedata, difflib

def words(s):
    s=unicodedata.normalize("NFKC",s.replace("﻿",""))
    # 引用符・ダッシュの字形の違い(’ と ')を誤りにしない。最初の採点では benjamin’s などが全撮影で誤りになっていた
    s=s.translate(str.maketrans({"’":"'","‘":"'","“":'"',"”":'"',"–":"-","—":"-"}))
    toks=[re.sub(r"^[^\w]+|[^\w]+$","",t.lower()) for t in s.split()]
    return [t for t in toks if t]

def read_vector(gt_text, hyp_text):
    g=words(gt_text); h=words(hyp_text)
    ok=[0]*len(g)
    sm=difflib.SequenceMatcher(None,g,h,autojunk=False)
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): ok[a+k]=1
    return g, ok

if __name__=="__main__":
    # 自己テスト
    g,ok=read_vector("The quick brown fox, jumps.","the quick brwn fox jumps")
    assert g==["the","quick","brown","fox","jumps"] and ok==[1,1,0,1,1], (g,ok)
    g,ok=read_vector("ﬁeld effect","field effect extra"); assert ok==[1,1], ok
    g,ok=read_vector("a b c d","a c d"); assert ok==[1,0,1,1], ok
    print("score_words self-test ok")

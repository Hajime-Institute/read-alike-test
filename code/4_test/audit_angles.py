# -*- coding: utf-8 -*-
"""同じ文書・同じ焦点の設定の撮影(正面の S_ と角度違いの M_ 5 枚)を、すべて確かめる側にも使う。
各撮影について、生成器の設定を A1 の手順(20 語ずつの偶数番目の塊で帯ごとの正答率の並びを合わせる)で選び、
奇数番目の塊で κ を出す。上限は、その撮影と同じ組の残りの撮影との κ の平均(同じ語で測る)。
本物は四隅で貼り直したページを段落の枠ごとに読んだもの(rect_)。読み手が確かめ側の語の 3% 以上を落とす撮影だけを使う。
使い方: python -I audit_angles.py <smartdoc_pilot> <tessblk|doctrblk>  (環境変数 PH=WP|Android、OB=Ob820 など)"""
import sys, os, json, re, itertools, zlib, statistics as st
B=sys.argv[1]; READER=sys.argv[2]
sys.path.insert(0,B+"/code"); from score_words import read_vector; from bootdoc import boot_doc, ndocs; from word_xy import word_xy
FN={"tessblk":"raw_tess_blocks.jsonl","doctrblk":"raw_doctr_blocks.jsonl","visionblk":"raw_vision_blocks.jsonl","vlmblk":"raw_vlm_blocks.jsonl"}[READER]
PH=os.environ.get("PH","WP"); OB=os.environ.get("OB","Ob820"); LIGHT=os.environ.get("LIGHT","L2")   # 照明(L2 昼光と天井灯 / L3 夜と卓上灯 / L4 卓上灯と物の影)
T={}
for l in open(f"{B}/results/{FN}"):
    r=json.loads(l)
    if r["tag"]!="blocks": continue
    k=r["image"].rsplit(".",1)[0]
    if k in T: continue
    d=re.search(r"_D(\d+)_",k).group(1); T[k]=read_vector(open(f"{B}/data_smartdoc/Ground_truth/page_{d}.txt",encoding="utf-8").read(),r["text"])[1]
CH=int(os.environ.get("CH","20")); NB=int(os.environ.get("NB","5"))   # 選ぶ語と測る語を交互に分ける塊の語数・ページを上から分ける帯の数(設計の感度は design_sensitivity.py)
ACC_LO=float(os.environ.get("ACC_LO","0.03"))   # 使う検査画像: 測る語での正答率が ACC_LO 以上 1−ACC_LO 以下
def acc(v): return sum(v)/max(1,len(v))
def kappa(a,b):
    n=len(a); po=sum(x==y for x,y in zip(a,b))/n; pa=sum(a)/n; pb=sum(b)/n; pe=pa*pb+(1-pa)*(1-pb); return (po-pe)/(1-pe) if pe<0.999 else float("nan")
PROF=os.environ.get("PROF","y5")   # y5: 文書の順に 5 つの帯 / xy10: 上下 5 × 左右 2 の区画(行の中の位置で左右を分ける)
XY={d:word_xy(open(f"{B}/data_smartdoc/Ground_truth/page_{d}.txt",encoding="utf-8").read()) for d in range(1,11)}
def prof(v,idx,n,d=None):
    if PROF=="xy10":
        bins=[[] for _ in range(2*NB)]
        for i in idx: x,y=XY[d][i]; bins[min(NB-1,int(y*NB))*2+(x>=0.5)].append(v[i])
    else:
        bins=[[] for _ in range(NB)]
        for i in idx: bins[min(NB-1,i*NB//n)].append(v[i])
    return [acc(b) if b else 1.0 for b in bins]
GENS={"ours_plane2":"defocusplanec","ours_plane":"defocusplane","ours_var":"defocusvar","ours_uni":"defocus","albDefocus":"albDefocus","albGauss":"albGauss","augDepth":"augDepth"}
if LIGHT=="L3" and os.environ.get("GENSET")!="light":   # 卓上灯の下のピンぼけ: 傾いた紙のぼけに卓上灯の照明を重ねた生成器も比べる
    GENS["ours_lampdef"]="lampdef"
if os.environ.get("GENSET")=="light":   # 低照度(L3): 卓上灯の撮影の生成器・照明の傾きだけ・一様な暗さ・albumentations・Augraphy
    GENS={"ours_plane":"lamp","ours_grad":"lightplane","ours_uni":"lightuni","albBright":"albBright","augLight":"augLight"}
res={g:[] for g in GENS}; dacc={g:[] for g in GENS}; ceil=[]; diff={g:[] for g in GENS}; used=0
caps={}
for k,v in T.items():
    # 同じ文書・同じ焦点の設定の撮影を一つの組にする: 正面の撮影(S_)と角度違いの撮影(M_)
    m=re.match(rf"rect_(S|M)_Img_{PH}_D(\d+)_{LIGHT}_r35_(a-?\d+_b-?\d+)" + ("" if OB=="none" else f"_{OB}") + "$",k)   # OB=none はピントの合った撮影(末尾の印なし)
    if m: caps.setdefault(int(m.group(2)),{})[m.group(1)+"_"+m.group(3)]=v
XMODE=os.environ.get("XDOC","0")   # 0: 撮影ごとに選ぶ / 1: 文書 1–5 の撮影でまとめて一つ選び、文書 6–10 に当てる / lodo: 確かめる文書を除いた全文書の撮影で選ぶ
XDOC=XMODE=="1"; LODO=XMODE=="lodo"
CAP=[]   # (文書, 角度, 本物の読み, 選ぶ語, 測る語, 上限)
LABEL_OUT=os.environ.get("LABEL_OUT")   # 読めない語の正解としての一致を数える(判定には効かない): 出どころ・本物の撮影で読めない語の数・出どころで読めない語の数・両方で読めない語の数
def label_rec(src,d,ang,re_,se,w=1.0):
    if not LABEL_OUT: return
    sm=sum(1-x for x in se); rm=sum(1-x for x in re_); both=sum((1-x)*(1-y) for x,y in zip(re_,se))
    open(LABEL_OUT,"a").write(json.dumps({"reader":READER,"ph":PH,"ob":OB,"light":LIGHT,"sel":os.environ.get("SEL","prof"),"src":src,"d":d,"ang":ang,"n":len(re_),"real_missed":rm*w,"src_missed":sm*w,"both":both*w})+"\n")
SEL=os.environ.get("SEL","prof")   # prof: 帯ごとの正答率の並びで選ぶ(提案の手順) / acc: 全体の正答率だけで選ぶ(素直なやり方)
MASK=os.environ.get("MASK","clean")   # clean: 綺麗な合成で読めた語 / sharp: それに加えて、同じ文書の鮮明な本物の撮影(正面)でも読めた語
for d,angs in sorted(caps.items()):
    cl=T.get(f"syn_D{d}_{PH}_none_0")
    if cl is None: continue
    if MASK=="sharp":
        sh=T.get(f"rect_S_Img_{PH}_D{d}_L2_r35_a0_b0")
        if sh is None or len(sh)!=len(cl): continue
        cl=[c and s for c,s in zip(cl,sh)]
    for ang,rv in sorted(angs.items()):
        if len(rv)!=len(cl): continue
        n=len(rv); sel=[i for i in range(n) if cl[i] and (i//CH)%2==0]; ev=[i for i in range(n) if cl[i] and (i//CH)%2==1]
        if os.environ.get("SPLIT")=="0":   # 分けない(比べのため): 対象の語すべてで選び、同じ語で一致を測る
            sel=ev=[i for i in range(n) if cl[i]]
        re_=[rv[i] for i in ev]
        if 1-acc(re_)<ACC_LO or acc(re_)<ACC_LO: continue
        if os.environ.get("DOCS") and not (int(os.environ["DOCS"].split("-")[0])<=d<=int(os.environ["DOCS"].split("-")[1])): continue   # 読み手がほとんど落とさない撮影も、ほとんど読めない撮影も使わない(どちらも一致を測れない)
        sib=[kappa(re_,[ov[i] for i in ev]) for oa,ov in angs.items() if oa!=ang and len(ov)==n]
        sib=[x for x in sib if x==x]
        if not sib: continue
        CAP.append((d,ang,rv,sel,ev,st.mean(sib)))
        if LABEL_OUT:
            sibs=[ov for oa,ov in angs.items() if oa!=ang and len(ov)==n]
            for ov in sibs: label_rec("recapture",d,ang,re_,[ov[i] for i in ev],1.0/len(sibs))
def cands(d,kn,n): 
    pre=f"syn_D{d}_{PH}_{kn}_"; return {kk[len(pre):]:v for kk,v in T.items() if kk.startswith(pre) and len(v)==n}
for d,ang,rv,sel,ev,c in CAP:
    if XDOC and d<=5: continue
    ceil.append((d,c)); used+=1
CHOSEN={}
NULL_DRAWS=int(os.environ.get("NULL_DRAWS","200"))
if os.environ.get("NULL")=="1":
    import random as _r
    GENS=dict(GENS); GENS["null_band"]=None; res["null_band"]=[]; dacc["null_band"]=[]; diff["null_band"]=[]
    for d,ang,rv,sel,ev,c in CAP:
        if XDOC and d<=5: continue
        n=len(rv); pr=prof(rv,sel,n,d); re_=[rv[i] for i in ev]
        band=lambda i: min(NB-1,i*NB//n)
        rnd=_r.Random(zlib.crc32(f"{d}|{ang}".encode())); ks=[]; accs=[]   # 乱数の種は文書と角度から決める(hash は実行ごとに変わるので使わない)
        for _ in range(NULL_DRAWS):
            se=[1 if rnd.random()<pr[band(i)] else 0 for i in ev]; k=kappa(re_,se); label_rec("null_band",d,ang,re_,se,1.0/NULL_DRAWS)
            if k==k: ks.append(k)
            accs.append(acc(se))
        kp=st.mean(ks) if ks else float("nan")
        res["null_band"].append((d,kp)); dacc["null_band"].append(abs(st.mean(accs)-acc(re_))); diff["null_band"].append((d,kp-c))
for g,kn in GENS.items():
    if kn is None: continue
    cs_all={d:cands(d,kn,len(rv)) for d,_,rv,_,_,_ in CAP}
    common=set.intersection(*[set(v) for v in cs_all.values()]) if cs_all and all(cs_all.values()) else set()
    def pick(cal):
        return min(sorted(common),key=lambda p: sum(sum((x-y)**2 for x,y in zip(prof(cs_all[d][p],sel,len(rv),d),prof(rv,sel,len(rv),d))) for d,_,rv,sel,_,_ in cal))
    if (XDOC or LODO) and not common: continue
    if XDOC:
        cal=[x for x in CAP if x[0]<=5]
        if not cal: continue
        best=pick(cal); CHOSEN[g]=best; print(f"  [{g}] 文書 1–5 で選んだ一つの設定: {best}")
    if LODO: bestd={d:pick([x for x in CAP if x[0]!=d]) for d in {x[0] for x in CAP}}
    for d,ang,rv,sel,ev,c in CAP:
        if XDOC and d<=5: continue
        n=len(rv); re_=[rv[i] for i in ev]; cs=cands(d,kn,n)
        if not cs: continue
        if XDOC: b=best
        elif LODO: b=bestd[d]
        elif SEL=="acc":   # 素直なやり方: 選ぶ語での正答率が本物に一番近い設定(問題設定の節の答え方)
            ar=acc([rv[i] for i in sel]); b=min(cs,key=lambda x: abs(acc([cs[x][i] for i in sel])-ar))
        else:
            pr=prof(rv,sel,n,d); b=min(cs,key=lambda x: sum((p-q)**2 for p,q in zip(prof(cs[x],sel,n,d),pr)))
        se=[cs[b][i] for i in ev]; kp=kappa(re_,se); label_rec(g,d,ang,re_,se)
        if os.environ.get("DUMP_CHOICE"): open(os.environ["DUMP_CHOICE"],"a").write(f"{g}\t{d}\t{ang}\t{b}\t{acc(re_):.3f}\t{acc(se):.3f}\t{kp:.3f}\t{c:.3f}\n")   # 調べるため: 選んだ設定を書き出す(判定には効かない)
        res[g].append((d,kp)); dacc[g].append(abs(acc(se)-acc(re_))); diff[g].append((d,kp-c))
print(f"reader {READER} {PH} {OB} PROF={PROF} XDOC={XMODE} MASK={MASK}: 確かめた撮影 {used}（文書 {ndocs(ceil)}）")
if not ceil:   # 読み手が判定に使える撮影が一枚も無い: 判定を出さずに記録だけ残す
    if os.environ.get("JSON_OUT"): json.dump({"rule":os.environ.get("RULE","equiv"),"light":LIGHT,"reader":READER,"phone":PH,"setting":OB,"n_captures":0,"n_docs":0},open(os.environ["JSON_OUT"],"w",encoding="utf-8"))
    sys.exit(0)
lo,hi=boot_doc(ceil)
# 許す差 δ: 本物どうしの κ の文書の間のばらつき(文書ごとの上限の平均の標準偏差)。生成器の結果は使わない
per={}
for d,c in ceil: per.setdefault(d,[]).append(c)
DELTA=st.stdev([st.mean(v) for v in per.values()]) if len(per)>1 else float("nan")
print(f"{'本物どうし(同じ文書の残りの角度)':16s} κ {st.mean(x for _,x in ceil):.2f} [{lo:.2f},{hi:.2f}]  δ={DELTA:.3f}")
RULE=os.environ.get("RULE","equiv")   # equiv: 幅 δ を両側に使う(区間の下端が -δ より上なら通る、上端が -δ より下なら落ちる) / R0: 旧の規則(上端が 0 より下なら落ちる)
def verdict(dl,dh):
    if RULE=="R0": return "落ちる" if dh<0 else ("通る" if dl>-DELTA else "決まらない")
    return "通る" if dl>-DELTA else ("落ちる" if dh<-DELTA else "決まらない")
OUTJ={"rule":RULE,"light":LIGHT,"sel":SEL,"reader":READER,"phone":PH,"setting":OB,"xdoc":XMODE,"mask":MASK,"n_captures":used,"n_docs":ndocs(ceil),
      "ceiling":{"mean":st.mean(x for _,x in ceil),"ci":[lo,hi]},"delta":DELTA,"gens":{}}
for g in GENS:
    xs=[x for _,x in res[g] if x==x]
    if not xs: print(f"{g:12s} no data"); continue
    lo,hi=boot_doc(res[g]); dl,dh=boot_doc(diff[g])
    print(f"{g:12s} n={len(xs):3d} κ {st.mean(xs):.2f} [{lo:.2f},{hi:.2f}] |Δacc| {st.mean(dacc[g]):.3f} | κ−上限 {st.mean(x for _,x in diff[g] if x==x):+.2f} [{dl:+.2f},{dh:+.2f}] {verdict(dl,dh)}")
    OUTJ["gens"][g]={"n":len(xs),"kappa":{"mean":st.mean(xs),"ci":[lo,hi]},"abs_dacc":st.mean(dacc[g]),
                     "diff":{"mean":st.mean(x for _,x in diff[g] if x==x),"ci":[dl,dh]},"verdict":verdict(dl,dh),"chosen":CHOSEN.get(g)}
if os.environ.get("POS")=="1":
    OUTJ["roles"]={}
    for role in sorted({a for _,angs in caps.items() for a in angs}):
        dd=[]
        for d,ang,rv,sel,ev,c in CAP:
            if XDOC and d<=5: continue
            if ang==role: continue
            n=len(rv); re_=[rv[i] for i in ev]; angs=caps[d]
            if role not in angs or len(angs[role])!=n: continue
            kr=kappa(re_,[angs[role][i] for i in ev])
            rest=[kappa(re_,[ov[i] for i in ev]) for oa,ov in angs.items() if oa not in (ang,role) and len(ov)==n]
            rest=[x for x in rest if x==x]
            if kr!=kr or not rest: continue
            dd.append((d,kr-st.mean(rest)))
        if ndocs(dd)<2: continue
        dl,dh=boot_doc(dd); m=st.mean(x for _,x in dd)
        OUTJ["roles"][role]={"n":len(dd),"diff":{"mean":m,"ci":[dl,dh]},"verdict":verdict(dl,dh)}
        print(f"  real capture {role:12s} as generator: n={len(dd):3d} diff {m:+.3f} [{dl:+.3f},{dh:+.3f}] {verdict(dl,dh)}")
if os.environ.get("JSON_OUT"):
    json.dump(OUTJ,open(os.environ["JSON_OUT"],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
if LODO:
    for g,kn in GENS.items():
        pass

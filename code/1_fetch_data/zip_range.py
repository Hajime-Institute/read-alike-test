# -*- coding: utf-8 -*-
"""SmartDoc-QA の zip(13.7GB, Zenodo, CC BY 4.0)から、必要なファイルだけを HTTP の範囲指定で取り出す。
使い方: python -I zip_range.py <central_directory.bin> <出力先> <正規表現> [--list]
central_directory.bin は zip の末尾の目次(取得済み)。zip64 の拡張欄に対応。"""
import re, struct, sys, os, zlib, urllib.request
URL="https://zenodo.org/records/5293201/files/Dataset%20SmartDoc-QA.zip?download=1"

def entries(cd):
    p=0
    while True:
        p=cd.find(b'PK\x01\x02',p)
        if p<0: return
        method,=struct.unpack('<H',cd[p+10:p+12])
        csize,usize=struct.unpack('<II',cd[p+20:p+28])
        nlen,elen,clen=struct.unpack('<HHH',cd[p+28:p+34])
        off,=struct.unpack('<I',cd[p+42:p+46])
        name=cd[p+46:p+46+nlen].decode('utf-8','replace'); ex=cd[p+46+nlen:p+46+nlen+elen]
        q=0                                    # zip64 拡張欄(id=1): 0xFFFFFFFF の欄だけが順に 8 バイトで入る
        while q+4<=len(ex):
            hid,hsz=struct.unpack('<HH',ex[q:q+4]); body=ex[q+4:q+4+hsz]; k=0
            if hid==1:
                if usize==0xFFFFFFFF: usize,=struct.unpack('<Q',body[k:k+8]); k+=8
                if csize==0xFFFFFFFF: csize,=struct.unpack('<Q',body[k:k+8]); k+=8
                if off==0xFFFFFFFF: off,=struct.unpack('<Q',body[k:k+8]); k+=8
            q+=4+hsz
        yield dict(name=name,method=method,csize=csize,usize=usize,off=off,nlen=nlen,elen=elen)
        p+=46+nlen+elen+clen

def fetch(a,b,tries=4):
    # 通信が途中で切れることがある(IncompleteRead)。数回取り直す
    for t in range(tries):
        try:
            req=urllib.request.Request(URL,headers={"Range":f"bytes={a}-{b}"})
            with urllib.request.urlopen(req,timeout=120) as r: return r.read()
        except Exception as ex:
            if t==tries-1: raise
            import time; time.sleep(3*(t+1))

def extract(e,outdir):
    raw=fetch(e["off"], e["off"]+30+e["nlen"]+e["elen"]+e["csize"]+4096)
    assert raw[:4]==b'PK\x03\x04', "local header not found"
    nlen,elen=struct.unpack('<HH',raw[26:30]); start=30+nlen+elen
    data=raw[start:start+e["csize"]]
    if e["method"]==8: data=zlib.decompress(data,-15)
    elif e["method"]!=0: raise ValueError(f"method {e['method']}")
    assert len(data)==e["usize"], (len(data),e["usize"])
    rel=e["name"].split("/",1)[1] if "/" in e["name"] else e["name"]
    path=os.path.join(outdir,rel); os.makedirs(os.path.dirname(path),exist_ok=True)
    open(path,"wb").write(data); return path

if __name__=="__main__":
    cd=open(sys.argv[1],'rb').read(); out=sys.argv[2]; pat=re.compile(sys.argv[3])
    sel=[e for e in entries(cd) if pat.search(e["name"]) and not e["name"].endswith("/")]
    if "--list" in sys.argv:
        for e in sel: print(e["name"],e["usize"])
        print(len(sel),"files",sum(e["csize"] for e in sel)//1024,"KB compressed"); sys.exit()
    for e in sel:
        rel=e["name"].split("/",1)[1] if "/" in e["name"] else e["name"]
        if os.path.exists(os.path.join(out,rel)) and os.path.getsize(os.path.join(out,rel))==e["usize"]: continue   # 取得済み
        print(extract(e,out),flush=True)

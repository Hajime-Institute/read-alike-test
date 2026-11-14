# -*- coding: utf-8 -*-
"""設定を一つに固めてよいかの検査(合成で評価用のデータを作るときの使い方): 確かめる文書を除いた残りの文書の撮影で設定を一つ選び、
その文書の撮影に当てる(文書を一つずつ外す)。ぼけ 12 条件 × 読み手 4。結果は results/facts_lodo.json。
使い方: python -I run_lodo.py <smartdoc_pilot>"""
import sys, os, json, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
B = sys.argv[1]; PY = sys.executable
CELLS = [(ph, ob, L, f"{lab} {L}") for ph, ob, lab in (("WP","Ob820","Nokia 1"),("WP","Ob940","Nokia 2"),("Android","Ob1","Samsung 1"),("Android","Ob2","Samsung 2")) for L in ("L2","L3","L4")]
READERS = [("tessblk","Tesseract"),("doctrblk","docTR"),("visionblk","Vision"),("vlmblk","Mistral")]
def run(j):
    ph, ob, L, lab, rd, rl = j
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f: out = f.name
    env = dict(os.environ, PH=ph, OB=ob, LIGHT=L, MASK="sharp", XDOC="lodo", SEL="prof", JSON_OUT=out, NULL="0", POS="0", GENSET="")
    p = subprocess.run([PY, "-I", f"{B}/code/audit_angles.py", B, rd], env=env, capture_output=True)
    return f"{lab}|{rl}", (json.load(open(out)) if p.returncode == 0 else {"error": p.stderr.decode()[-300:]})
R = {}
with ThreadPoolExecutor(6) as ex:
    for k, res in ex.map(run, [(*c, rd, rl) for c in CELLS for rd, rl in READERS]): R[k] = res; print(k, "error" if "error" in res else "ok", flush=True)
json.dump(R, open(f"{B}/results/facts_lodo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("LODO_DONE")

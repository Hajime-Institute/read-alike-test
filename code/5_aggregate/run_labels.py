# -*- coding: utf-8 -*-
"""読めない語の正解としての一致を、ぼけ 12 条件 × 読み手 4 × 選び方 2(帯・誤り率)で数える。判定の JSON も同じ設定で書き出し、facts と照らせるようにする。
環境は make_facts.py と同じ(MASK=sharp、帯で選ぶ回だけ帰無の対照と本物の対照を付ける)。
使い方: python3 -I run_labels.py <作業ディレクトリ(code/ results/ data_smartdoc/ を持つ)> <並列数>"""
import sys, os, json, subprocess
from concurrent.futures import ThreadPoolExecutor
B = sys.argv[1]; NP = int(sys.argv[2]) if len(sys.argv) > 2 else 4
CELLS = [(ph, ob, L, f"{lab} {L}") for ph, ob, lab in (("WP", "Ob820", "Nokia 1"), ("WP", "Ob940", "Nokia 2"), ("Android", "Ob1", "Samsung 1"), ("Android", "Ob2", "Samsung 2")) for L in ("L2", "L3", "L4")]
READERS = [("tessblk", "Tesseract"), ("doctrblk", "docTR"), ("visionblk", "Vision"), ("vlmblk", "Mistral")]
os.makedirs(f"{B}/out", exist_ok=True)
def run(j):
    ph, ob, L, lab, rd, rl, sel = j
    tag = f"{lab.replace(' ', '_')}__{rl}__{sel}"; full = sel == "prof"
    env = dict(os.environ, PH=ph, OB=ob, LIGHT=L, MASK="sharp", XDOC="0", SEL=sel, NULL="1" if full else "0", POS="1" if full else "0", GENSET="",
               JSON_OUT=f"{B}/out/{tag}.json", LABEL_OUT=f"{B}/out/{tag}.labels.jsonl")
    for f in (env["JSON_OUT"], env["LABEL_OUT"]):
        if os.path.exists(f): os.remove(f)
    r = subprocess.run([sys.executable, "-I", f"{B}/code/audit_angles.py", B, rd], env=env, capture_output=True)
    return tag, r.returncode, r.stderr.decode()[-200:]
jobs = [(ph, ob, L, lab, rd, rl, sel) for ph, ob, L, lab in CELLS for rd, rl in READERS for sel in ("prof", "acc")]
with ThreadPoolExecutor(NP) as ex:
    for tag, rc, err in ex.map(run, jobs): print(tag, "ok" if rc == 0 else "ERR " + err, flush=True)
print("RUN_LABELS_DONE", flush=True)

# -*- coding: utf-8 -*-
"""卓上灯の生成器を全文書・両機種で作る(make_lamp.py を並列に回す)。
lamp: 低照度(ピントの合った L3)の候補、格子のすべて(80 通り)
lampdef: 卓上灯の下のピンぼけ(L3 の Ob 条件)の候補。傾いた紙のぼけの上下の半径(Nokia 8×8、Samsung 7×7 組)× インクの明るさ 5 通り
(光の落ち方は低照度の格子の中ほど a_v 0.5・a_h 0.25 に固め、線の柔らかさはぼけに任せて 0)
使い方: python -I gen_lamp.py <smartdoc_pilot> <degrade_lab> <出力先>"""
import sys, subprocess, os
from concurrent.futures import ThreadPoolExecutor
B, LAB, OUT = sys.argv[1:4]; PY = sys.executable
PH = {"WP": ("208", (-6, -4, -2, 0, 2, 4, 6, 8)), "Android": ("285", (-6, -3, 0, 3, 6, 9, 12))}
LAMPS = ["0.5:0.25:1:0.15:0:6", "0.5:0.25:1:0.3:0:6", "0.5:0.25:1:0.45:0:6", "0.5:0.25:1:0.6:0:6", "0.5:0.25:1:0.75:0:6"]
jobs = []
for ph, (dpi, R) in PH.items():
    for d in range(1, 11):
        jobs.append(({}, [dpi, ph, str(d)]))
        for t in R:
            for b in R: jobs.append(({"DEFOCUS": f"{t}:{b}"}, [dpi, ph, str(d)] + LAMPS))
def go(j):
    env, a = j
    p = subprocess.run([PY, "-I", f"{B}/code/make_lamp.py", LAB, OUT] + a, env=dict(os.environ, **env), capture_output=True, text=True)
    return p.returncode, (p.stderr or "")[-200:], a[:3], env
bad = 0
with ThreadPoolExecutor(5) as ex:
    for rc, err, a, env in ex.map(go, jobs):
        if rc: bad += 1; print("ERROR", a, env, err, flush=True)
print("jobs", len(jobs), "errors", bad, flush=True)
print("GEN_LAMP_DONE", flush=True)

# -*- coding: utf-8 -*-
"""二つ目のセット(元の PDF の無い文書)の合成画像: 貼り直したピントの合った正面の撮影を元の画像にして、
傾いた紙のぼけ(degrade_lab の f_defocus_plane)を本文と同じ候補の設定でかける。灰色にして JPEG 90 で保存する(本文の合成と同じ)。
使い方: python -I gen_letters.py <degrade_lab> <results> <候補の json> <文書番号...>"""
import sys, os, json, cv2
lab, R, cj = sys.argv[1:4]; docs = sys.argv[4:]
sys.path.insert(0, lab); import degrade as D
C = json.load(open(cj)); out = os.path.join(R, "synth_letters"); os.makedirs(out, exist_ok=True)
for d in docs:
    for ph in ("WP", "Android"):
        src = os.path.join(R, "real_rect", f"rect_S_Img_{ph}_D{d}_L2_r35_a0_b0.png")
        if not os.path.exists(src): print("no source", src, flush=True); continue
        clean = cv2.cvtColor(cv2.cvtColor(cv2.imread(src), cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        for v in C[f"{ph}|defocusplane"]:
            p = os.path.join(out, f"syn_D{d}_{ph}_defocusplane_{v}.jpg")
            if os.path.exists(p): continue
            t, b = [float(x) for x in v.split(":")[:2]]
            im = D.f_defocus_plane(clean, t, b, color=False)
            ok, enc = cv2.imencode(".jpg", im, [int(cv2.IMWRITE_JPEG_QUALITY), 90]); open(p, "wb").write(enc.tobytes())
        print("done", d, ph, flush=True)

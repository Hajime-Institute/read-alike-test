# -*- coding: utf-8 -*-
"""卓上灯の撮影(SmartDoc-QA の L3)を、撮影の仕組みに沿って作る生成器 lamp。元の PDF を機種の解像度で灰色の画像にして次をかけ、JPEG 90 で保存する。
1) 紙に当たる光: 灯は右上の外にあり、光は下へ a_v、左へ a_h の割合で落ちる  L(x, y) = hi (1 - a_h (1 - x)) (1 - a_v y)
2) インクの明るさ: 夜の撮影ではインクが黒くならず、紙の明るさの c 倍になる  反射 = c + (1 - c) 元の画素 / 255
3) 線の柔らかさ: ノイズ除去で線がわずかに鈍る(ガウスの σ = s 画素、0 ならかけない)
4) 撮像の雑音(σ = n、設定ごとに決まった種)
ぼけと重ねるとき(DEFOCUS=上の半径:下の半径)は、傾いた紙のぼけ(degrade_lab の f_defocus_plane)を先にかけてから 1)〜4) をかける。
使い方: python -I make_lamp.py <degrade_lab> <出力先> <dpi> <phone> <doc> [設定 a_v:a_h:hi:c:s:n ...](省略すると格子のすべて)"""
import sys, os, subprocess, tempfile, zlib, itertools, numpy as np, cv2
LAB, out, DPI, PHONE, doc = sys.argv[1:6]; given = sys.argv[6:]
HERE = os.path.dirname(os.path.abspath(__file__)); os.makedirs(out, exist_ok=True)
GRID = [f"{av:g}:{ah:g}:1:{c:g}:{s:g}:6" for av, ah, c, s in itertools.product((0.4, 0.6), (0.15, 0.35), (0.15, 0.25, 0.35, 0.45, 0.55), (0, 0.5, 1.0, 1.5))]
DEF = os.environ.get("DEFOCUS", "")
tmp = tempfile.mkdtemp(); subprocess.run(["pdftoppm", "-r", DPI, "-gray", "-png", "-singlefile",
    os.path.join(HERE, "..", "data_smartdoc", "Original_documents", f"page_{doc}.pdf"), tmp + "/p"], check=True, capture_output=True)
g = cv2.imread(tmp + "/p.png", cv2.IMREAD_GRAYSCALE)
if DEF:
    sys.path.insert(0, LAB); import degrade as D
    g = cv2.cvtColor(D.f_defocus_plane(cv2.cvtColor(g, cv2.COLOR_GRAY2BGR), *[float(x) for x in DEF.split(":")]), cv2.COLOR_BGR2GRAY)
g = g.astype(np.float32); h, w = g.shape
y, x = np.mgrid[0:h, 0:w].astype(np.float32); x /= (w - 1); y /= (h - 1)
for v in (given or GRID):
    av, ah, hi, c, s, n = (float(t) for t in v.split(":"))
    name = f"syn_D{doc}_{PHONE}_{'lampdef' if DEF else 'lamp'}_{(DEF + '+') if DEF else ''}{v}.jpg"
    dst = os.path.join(out, name)
    if os.path.exists(dst): continue
    im = 255 * hi * (1 - ah * (1 - x)) * (1 - av * y) * (c + (1 - c) * g / 255)
    if s > 0: im = cv2.GaussianBlur(im, (0, 0), s)
    if n > 0: im = im + np.random.default_rng(zlib.crc32(name.encode())).normal(0, n, im.shape).astype(np.float32)
    ok, enc = cv2.imencode(".jpg", np.clip(im, 0, 255).astype(np.uint8), [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    open(dst, "wb").write(enc.tobytes())
print("doc", doc, PHONE, "done", len(given or GRID), flush=True)

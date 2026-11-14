# -*- coding: utf-8 -*-
"""低照度(夜・卓上灯、SmartDoc-QA の L3)の合成を作る。元の PDF を機種の解像度で灰色の画像にし、照明を掛けて JPEG 90 で保存する。
lightplane: 照明の強さをページの右上(灯のある側)から左下へ一次式で落とす(明るい角 hi・暗い角 lo)。雑音 σ を足す。撮影の仕組みに沿う生成器
lightuni:   ページ全体を同じ強さ L で暗くし、雑音 σ を足す(素直な生成器)
albBright:  albumentations 2.0.8 の RandomBrightnessContrast(明るさ・コントラストを固定)と GaussNoise
augLight:   Augraphy 8.2.6 の LightingGradient(乱数の種を固定)
照明は紙の明るさに掛ける(インクの黒はほぼ黒のまま、地の白が暗くなる)。雑音は乱数の種を設定ごとに固定。
使い方: <.venv_aug>/bin/python -I make_lowlight.py <出力先> <dpi> <phone> <doc...>"""
import sys, os, subprocess, tempfile, random, zlib, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); out, DPI, PHONE = sys.argv[1:4]; docs = sys.argv[4:]
os.makedirs(out, exist_ok=True)
def plane(h, w, hi, lo):
    # 右上の角(x=1, y=0)で hi、左下の角(x=0, y=1)で lo。対角線に沿う一次式
    y, x = np.mgrid[0:h, 0:w].astype(np.float32); t = ((1 - x / (w - 1)) + y / (h - 1)) / 2
    return hi + (lo - hi) * t
def noise(im, s, seed):
    if s <= 0: return im
    rng = np.random.default_rng(seed); return im + rng.normal(0, s, im.shape).astype(np.float32)
SET = []
for hi in (0.6, 0.75, 0.9, 1.0):
    for lo in (0.2, 0.3, 0.4, 0.5, 0.6, 0.75):
        if lo >= hi: continue
        for s in (0, 4, 8, 12): SET.append(("lightplane", f"{hi:g}:{lo:g}:{s}", ("plane", hi, lo, s)))
for L in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
    for s in (0, 4, 8, 12): SET.append(("lightuni", f"{L:g}:{s}", ("uni", L, s)))
for b in (-0.6, -0.5, -0.4, -0.3, -0.2):
    for c in (-0.4, -0.2, 0.0):
        SET.append(("albBright", f"{b:g}:{c:g}", ("alb", b, c)))
for lo, hi in ((0.2, 0.6), (0.3, 0.8), (0.4, 1.0)):
    for seed in (0, 1, 2): SET.append(("augLight", f"{lo:g}-{hi:g}:s{seed}", ("aug", lo, hi, seed)))
for doc in docs:
    tmp = tempfile.mkdtemp(); subprocess.run(["pdftoppm", "-r", DPI, "-gray", "-png", "-singlefile",
        os.path.join(HERE, "..", "data_smartdoc", "Original_documents", f"page_{doc}.pdf"), tmp + "/p"], check=True, capture_output=True)
    g = cv2.imread(tmp + "/p.png", cv2.IMREAD_GRAYSCALE).astype(np.float32); h, w = g.shape
    for kind, param, spec in SET:
        dst = os.path.join(out, f"syn_D{doc}_{PHONE}_{kind}_{param}.jpg")
        if os.path.exists(dst): continue
        seed = zlib.crc32(f"{doc}|{PHONE}|{kind}|{param}".encode())   # 設定ごとに決まった種
        if spec[0] == "plane": im = noise(g * plane(h, w, spec[1], spec[2]), spec[3], seed)
        elif spec[0] == "uni": im = noise(g * spec[1], spec[2], seed)
        elif spec[0] == "alb":
            import albumentations as A
            random.seed(0); np.random.seed(0)
            t = A.Compose([A.RandomBrightnessContrast(brightness_limit=(spec[1], spec[1]), contrast_limit=(spec[2], spec[2]), p=1.0),
                           A.GaussNoise(std_range=(0.03, 0.03), p=1.0)], seed=0)
            im = t(image=cv2.cvtColor(g.astype(np.uint8), cv2.COLOR_GRAY2BGR))["image"][..., 0].astype(np.float32)
        else:
            from augraphy import LightingGradient
            random.seed(spec[3]); np.random.seed(spec[3])
            t = LightingGradient(light_position=None, direction=None, max_brightness=int(255 * spec[2]), min_brightness=int(255 * spec[1]), mode="gaussian", linear_decay_rate=None, transparency=None, p=1)
            im = t(cv2.cvtColor(g.astype(np.uint8), cv2.COLOR_GRAY2BGR))
            im = (im[..., 0] if im.ndim == 3 else im).astype(np.float32)
        ok, enc = cv2.imencode(".jpg", np.clip(im, 0, 255).astype(np.uint8), [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        open(dst, "wb").write(enc.tobytes())
    print("doc", doc, "done", len(SET), flush=True)

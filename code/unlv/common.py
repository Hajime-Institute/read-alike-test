# -*- coding: utf-8 -*-
"""UNLV/ISRI パイロットの共通部品。
- ページ一覧・ゾーン(.uzn)・正解(.txt, ページ単位でゾーン順に連結済み)の読み込み
- ゾーンごとに切り出して Tesseract psm 6 で読み、ゾーン順に連結してページの書き起こしにする
- 結果は results/ に JSONL で全文を残す(条件ごとに 1 ファイル、1 行 = 1 ページ)
データ(data_unlv/)は読むだけ。そこから何も実行しない。"""
import os, re, io, json, glob, random, subprocess
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data_unlv")
RES = os.path.join(ROOT, "results")
TESS = "/opt/homebrew/bin/tesseract"
DPI = {"2B": 200, "3B": 300, "3A": 300, "4B": 400}
PAD = 0.05  # ゾーンの外側に足す白余白(インチ)。ゾーンの中身は広げない


def page_ids(tset):
    """data_unlv/<set>.2B/pages に並ぶページ ID(例 8500_001)と置き場のサブディレクトリ"""
    out = []
    with open(os.path.join(DATA, f"{tset}.2B", "pages")) as f:
        for line in f:
            p = line.split()
            if len(p) == 2:
                out.append((p[0].rsplit(".", 1)[0], p[1]))
    return out


def paths(tset, res, pid, sub):
    b = os.path.join(DATA, f"{tset}.{res}", sub, f"{pid}.{res}")
    return b + ".tif", b + ".uzn", b + ".txt"


def read_uzn(path):
    z = []
    with open(path, encoding="latin-1") as f:
        for line in f:
            p = line.split()
            if len(p) >= 5 and all(re.fullmatch(r"-?\d+", t) for t in p[:4]):
                x, y, w, h = map(int, p[:4])
                z.append({"box": [x, y, w, h], "type": " ".join(p[4:])})
    return z


def read_gt(path):
    with open(path, encoding="latin-1") as f:
        return f.read()


def load_gray(path):
    """1 bit TIFF を 0..255 の 8 bit 濃淡(白=255)にする"""
    return np.array(Image.open(path).convert("L"), dtype=np.uint8)


def sample_pages(tset, n, seed=0):
    ids = page_ids(tset)
    rnd = random.Random(seed)
    rnd.shuffle(ids)
    return ids[:n]


def ocr_crop(gray, box, dpi, psm=6):
    x, y, w, h = box
    H, W = gray.shape
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return ""
    crop = gray[y0:y1, x0:x1]
    p = int(round(PAD * dpi))
    crop = np.pad(crop, p, constant_values=255)
    buf = io.BytesIO()
    Image.fromarray(crop).save(buf, format="PNG", dpi=(dpi, dpi))
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    r = subprocess.run([TESS, "stdin", "stdout", "--psm", str(psm), "--dpi", str(dpi), "-l", "eng"],
                       input=buf.getvalue(), capture_output=True, env=env)
    return r.stdout.decode("utf-8", "replace")


def ocr_page(gray, zones, dpi, scale=1.0):
    """zones の座標に scale を掛けて(合成画像用)ゾーン順に読む"""
    out = []
    for i, z in enumerate(zones):
        b = [int(v * scale) for v in z["box"]] if scale != 1.0 else z["box"]
        out.append({"i": i, "type": z["type"], "box": b, "text": ocr_crop(gray, b, dpi)})
    return out


def write_jsonl(path, recs):
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


_FIXES = None


def apply_fix(tset, res, pid, gray):
    """results/orientation_fixes.json に載っている画像(配布時に 180 度回っていたもの)を直す。
    180 度回し、3B ゾーン座標に合うよう整数画素だけ平行移動(はみ出しは白で埋める)"""
    global _FIXES
    if _FIXES is None:
        p = os.path.join(RES, "orientation_fixes.json")
        _FIXES = json.load(open(p)) if os.path.exists(p) else {}
    fx = _FIXES.get(f"{tset}/{res}/{pid}")
    if not fx:
        return gray, None
    import cv2
    g = cv2.rotate(gray, cv2.ROTATE_180)
    dx, dy = fx["shift"]
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    g = cv2.warpAffine(g, M, (g.shape[1], g.shape[0]), flags=cv2.INTER_NEAREST, borderValue=255)
    return g, fx

# -*- coding: utf-8 -*-
"""Apple Vision の OCR(ocrmac、recognition_level=accurate、英語)を段落の枠ごとに読む(ocr_blocks.py と同じ枠)。
枠の中の行は、上から下・左から右の順につなぐ(Vision の座標は左下が原点)。
使い方: <venv>/bin/python -I ocr_vision_blocks.py <out.jsonl> <tag> <画像...>"""
import sys, os, json, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocr_blocks import blocks
from ocrmac import ocrmac
from PIL import Image
def read(path, tag):
    name = os.path.basename(path); d = re.search(r"_D(\d+)_", name).group(1)
    im = Image.open(path).convert("RGB"); W, H = im.size; m = 0.012; texts = []; t0 = time.time()
    for _, (x0, y0, x1, y1) in blocks(d):
        cr = im.crop((max(0, int((x0 - m) * W)), max(0, int((y0 - m) * H)), min(W, int((x1 + m) * W)), min(H, int((y1 + m) * H))))
        r = ocrmac.OCR(cr, recognition_level="accurate", language_preference=["en-US"]).recognize()
        r = sorted(r, key=lambda t: -(t[2][1] + t[2][3] / 2))   # 行の中心の高さで上から並べ、近いものを一つの行にまとめる
        groups = []
        for txt, conf, (x, y, w, h) in r:
            c = y + h / 2
            if groups and abs(c - groups[-1]["c"]) <= h * 0.5: groups[-1]["items"].append((x, txt))
            else: groups.append({"c": c, "items": [(x, txt)]})
        texts.append("\n".join(" ".join(t for _, t in sorted(g["items"])) for g in groups))   # 行の中は左から
    return dict(image=name, tag=tag, model="vision-blocks", model_version="Apple Vision (ocrmac accurate, en-US) per paragraph box from clean page",
                n_blocks=len(texts), text="\n".join(texts), latency_s=round(time.time() - t0, 1), ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
if __name__ == "__main__":
    out, tag, imgs = sys.argv[1], sys.argv[2], sys.argv[3:]
    done = set()
    if os.path.exists(out):
        for l in open(out): r = json.loads(l); done.add((r["image"], r["tag"]))
    for p in imgs:
        if (os.path.basename(p), tag) in done: continue
        rec = read(p, tag)
        with open(out, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# -*- coding: utf-8 -*-
"""取得した本物の撮影を、貼り直し(rectify_page.py) → Tesseract を段落ごと(ocr_blocks.py) → docTR を段落ごと(ocr_doctr_blocks.py)の順に回す。
済んだものは飛ばす(貼り直しは rect_*.png があれば、読みは記録に同じ画像と tag があれば)。
使い方: python -I process_real.py <smartdoc_pilot> <正規表現(Captured_Images の下のファイル名に当てる)>"""
import sys, os, re, json, subprocess, glob
B, PAT = sys.argv[1], re.compile(sys.argv[2])
PY = sys.executable; PYD = os.path.join(B, ".venv_doctr", "bin", "python")
imgs = sorted(p for p in glob.glob(f"{B}/data_smartdoc/Captured_Images/*/Images/*.jpg") if PAT.search(os.path.basename(p)))
RR = f"{B}/results/real_rect"
todo = [p for p in imgs if not os.path.exists(f"{RR}/rect_{os.path.basename(p)[:-4]}.png")]
print("images", len(imgs), "to rectify", len(todo), flush=True)
for i in range(0, len(todo), 40):
    subprocess.run([PY, "-I", f"{B}/code/rectify_page.py", RR] + todo[i:i + 40], check=True)
rect = [f"{RR}/rect_{os.path.basename(p)[:-4]}.png" for p in imgs]
rect = [p for p in rect if os.path.exists(p)]
def done(fn):
    s = set()
    if os.path.exists(fn):
        for l in open(fn):
            r = json.loads(l); s.add((r["image"], r["tag"]))
    return s
for script, fn, py in (("ocr_blocks.py", "raw_tess_blocks.jsonl", PY), ("ocr_doctr_blocks.py", "raw_doctr_blocks.jsonl", PYD)):
    d = done(f"{B}/results/{fn}"); rest = [p for p in rect if (os.path.basename(p), "blocks") not in d]
    print(script, "to read", len(rest), flush=True)
    for i in range(0, len(rest), 60):
        subprocess.run([py, "-I", f"{B}/code/{script}", f"{B}/results/{fn}", "blocks"] + rest[i:i + 60], check=True, stdout=subprocess.DEVNULL)
print("ok", flush=True)

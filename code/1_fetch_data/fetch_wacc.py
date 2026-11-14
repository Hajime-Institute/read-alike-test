# -*- coding: utf-8 -*-
"""SmartDoc-QA の zip から、データセットに付いた Tesseract の語の正答率(OCR_Accuracy_Tesseract/*.wacc.txt)を
機種ごとに一続きの範囲でまとめて取り、撮影ごとの正答率を results/smartdoc_wacc.json に書く(条件の見極め用)。
使い方: python -I fetch_wacc.py <smartdoc_pilot>"""
import sys, os, re, json, struct, zlib
B = sys.argv[1]; sys.path.insert(0, B + "/code")
from zip_range import entries, fetch
cd = open(B + "/data_smartdoc/_central_directory.bin", "rb").read()
E = [e for e in entries(cd) if "OCR_Accuracy_Tesseract" in e["name"] and e["name"].endswith(".wacc.txt")]
out = {}
for phone in ("Nokia_phone", "Samsung_phone"):
    es = sorted([e for e in E if f"/{phone}/" in e["name"]], key=lambda e: e["off"])
    a = es[0]["off"]; b = es[-1]["off"] + 30 + es[-1]["nlen"] + es[-1]["elen"] + es[-1]["csize"] + 4096
    buf = fetch(a, b)
    for e in es:
        p = e["off"] - a
        nlen, elen = struct.unpack("<HH", buf[p + 26:p + 30])
        data = buf[p + 30 + nlen + elen:p + 30 + nlen + elen + e["csize"]]
        txt = (zlib.decompress(data, -15) if e["method"] == 8 else data).decode("utf-8", "replace")
        m = re.search(r"([\d.]+)%\s+Accuracy", txt)
        out[os.path.basename(e["name"]).replace(".wacc.txt", "")] = float(m.group(1)) if m else None
    print(phone, len(es), "bytes", b - a)
json.dump(out, open(B + "/results/smartdoc_wacc.json", "w"), indent=0)
print("ok", len(out), sum(v is None for v in out.values()))

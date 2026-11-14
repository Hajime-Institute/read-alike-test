# -*- coding: utf-8 -*-
"""zip_range.py の取り出しを並列で回す(範囲指定の HTTP を同時に何本か張る)。取得済みは飛ばす。
使い方: python -I zip_range_par.py <central_directory.bin> <出力先> <正規表現> [並列数]"""
import sys, os, re
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zip_range import entries, extract
cd = open(sys.argv[1], "rb").read(); out = sys.argv[2]; pat = re.compile(sys.argv[3]); nw = int(sys.argv[4]) if len(sys.argv) > 4 else 8
sel = []
for e in entries(cd):
    if not pat.search(e["name"]) or e["name"].endswith("/"): continue
    rel = e["name"].split("/", 1)[1] if "/" in e["name"] else e["name"]
    p = os.path.join(out, rel)
    if os.path.exists(p) and os.path.getsize(p) == e["usize"]: continue
    sel.append(e)
print("to fetch", len(sel), flush=True)
def job(e):
    try: return extract(e, out)
    except Exception as ex: return f"ERROR {e['name']} {ex}"
with ThreadPoolExecutor(nw) as ex:
    for r in ex.map(job, sel): print(r, flush=True)
print("done", flush=True)

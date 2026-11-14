# -*- coding: utf-8 -*-
"""check_orientation.py で 180 度回っていた画像の直し方を決める。
直し方: 180 度回したあと、3B(同じ物理座標系の 3B ゾーンを使うため)に対する平行移動を
元の解像度で位相相関から求め、整数画素で移す。結果を results/orientation_fixes.json に書く。
ocr_run.py は読み込み時にこれを当てる。使い方: python -I make_fixes.py <set> [<set> ...]"""
import sys, os, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

fx_path = os.path.join(RES, "orientation_fixes.json")
fixes = json.load(open(fx_path)) if os.path.exists(fx_path) else {}
for tset in sys.argv[1:]:
    o = json.load(open(os.path.join(RES, f"orientation_{tset}.json")))
    subs = dict(page_ids(tset))
    for pid, d in o.items():
        for res, v in d.items():
            if not v["rot180"]:
                continue
            sub = subs[pid]
            img = cv2.rotate(load_gray(paths(tset, res, pid, sub)[0]), cv2.ROTATE_180).astype(np.float32)
            ref = load_gray(paths(tset, "3B", pid, sub)[0]).astype(np.float32)
            f = DPI[res] / 300.0
            ref = cv2.resize(ref, (int(round(ref.shape[1] * f)), int(round(ref.shape[0] * f))), interpolation=cv2.INTER_AREA)
            H, W = min(img.shape[0], ref.shape[0]), min(img.shape[1], ref.shape[1])
            win = cv2.createHanningWindow((W, H), cv2.CV_32F)
            (dx, dy), r = cv2.phaseCorrelate(255 - ref[:H, :W], 255 - img[:H, :W], win)
            fixes[f"{tset}/{res}/{pid}"] = {"rot180": True, "shift": [int(round(-dx)), int(round(-dy))], "pc_response": float(r)}
            print(tset, res, pid, fixes[f"{tset}/{res}/{pid}"])
with open(fx_path, "w") as f:
    json.dump(fixes, f, indent=1)

# -*- coding: utf-8 -*-
"""設計で決めた数(選ぶ語と測る語を交互に分ける塊の語数 20・帯の数 5・使う検査画像の正答率 3〜97%)を変えて、
判定を一から出し直す(設計の感度)。変えるのは一度に一つで、ほかは本文の値のまま。
audit_angles.py を、12 条件 × 読み手 4 × (帯で選ぶ・正答率で選ぶ・設定を一つに固定) で回し、変えた設定ごとに facts を書く。
数え方は design_sensitivity_summary.py(読み手の決まり・帰無の対照の決まりは write_tables.py と同じ)。
使い方: python -I design_sensitivity.py <読みと正解のあるディレクトリ> <出力ディレクトリ> [変えた設定の名前 ...] [-P 並列数]"""
import sys, os, json, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
args = sys.argv[1:]; P = 3
if "-P" in args: i = args.index("-P"); P = int(args[i + 1]); del args[i:i + 2]
B, OUT = args[0], args[1]; PY = sys.executable
VARIANTS = {"base": {},                                   # 本文の値(facts_defocus.json と一致することを確かめる)
            "ch10": {"CH": "10"}, "ch40": {"CH": "40"},   # 塊の語数
            "nosplit": {"SPLIT": "0"},                     # 分けない: 選ぶ語と測る語が同じ
            "nb3": {"NB": "3"}, "nb10": {"NB": "10"},      # 帯の数
            "acc01": {"ACC_LO": "0.01"}, "acc05": {"ACC_LO": "0.05"}, "acc10": {"ACC_LO": "0.10"}}   # 使う検査画像の正答率の範囲
names = args[2:] or list(VARIANTS)
CELLS = [(ph, ob, L, f"{lab} {L}") for ph, ob, lab in (("WP", "Ob820", "Nokia 1"), ("WP", "Ob940", "Nokia 2"), ("Android", "Ob1", "Samsung 1"), ("Android", "Ob2", "Samsung 2")) for L in ("L2", "L3", "L4")]
READERS = [("tessblk", "Tesseract"), ("doctrblk", "docTR"), ("visionblk", "Vision"), ("vlmblk", "Mistral")]
KINDS = {"per_capture": {"XDOC": "0", "SEL": "prof", "NULL": "1", "POS": "1"},   # make_facts.py と同じ
         "per_capture_select_by_accuracy": {"XDOC": "0", "SEL": "acc", "NULL": "0", "POS": "0"},
         "lodo": {"XDOC": "lodo", "SEL": "prof", "NULL": "0", "POS": "0"}}           # run_lodo.py と同じ
def run(job):
    name, kind, (ph, ob, L, lab), (rd, rl) = job
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f: out = f.name
    env = dict(os.environ, PH=ph, OB=ob, LIGHT=L, MASK="sharp", JSON_OUT=out, GENSET="", **KINDS[kind], **VARIANTS[name])
    r = subprocess.run([PY, "-I", f"{B}/code/audit_angles.py", B, rd], env=env, capture_output=True)
    if r.returncode != 0: return job, {"error": r.stderr.decode()[-300:]}
    x = json.load(open(out, encoding="utf-8")); os.unlink(out); return job, x
os.makedirs(OUT, exist_ok=True)
for name in names:
    dst = os.path.join(OUT, f"facts_{name}.json")
    if os.path.exists(dst): print("skip", name, flush=True); continue
    jobs = [(name, k, c, r) for k in KINDS for c in CELLS for r in READERS]
    F = {k: {} for k in KINDS}; err = 0
    with ThreadPoolExecutor(P) as ex:
        for (nm, kind, c, r), x in ex.map(run, jobs):
            F[kind][f"{c[3]}|{r[1]}"] = x; err += "error" in x
    F["cells"] = [c[3] for c in CELLS]; F["readers"] = [r[1] for r in READERS]; F["variant"] = {"name": name, **VARIANTS[name]}
    json.dump(F, open(dst + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(dst + ".tmp", dst)
    print(name, "done", len(jobs), "jobs", err, "errors", flush=True)
print("DESIGN_SENS_DONE")

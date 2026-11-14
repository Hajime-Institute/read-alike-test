# -*- coding: utf-8 -*-
"""DeepInfra(OpenAI 互換)の VLM(既定 Mistral-Small-3.2-24B-Instruct-2506、温度 0)で、段落の枠ごとに書き写す(ocr_blocks.py と同じ枠)。
枠は BLOCKS_JSON(文書ごとの [x0,y0,x1,y1] の比の並び)から読む。キーは環境変数 DEEPINFRA_API_KEY から読み、表示しない。
一つの画像の段落をすべて読めたときだけ記録する(読み損ねた画像は、次に回したときに読み直す)。
使い方: DEEPINFRA_API_KEY=... BLOCKS_JSON=<blocks_d1_10.json> python -I ocr_vlm_blocks.py <out.jsonl> <tag> <画像の一覧ファイル> [並列数]"""
import sys, os, json, re, time, base64, io, urllib.request, threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
OUT, TAG, LIST = sys.argv[1:4]; NW = int(sys.argv[4]) if len(sys.argv) > 4 else 24
MODEL = os.environ.get("VLM_MODEL", "mistralai/Mistral-Small-3.2-24B-Instruct-2506")
KEY = os.environ.get("DEEPINFRA_API_KEY") or sys.exit("set the environment variable DEEPINFRA_API_KEY")
BLOCKS = json.load(open(os.environ["BLOCKS_JSON"]))
PROMPT = ("This is an image of part of a printed document. Transcribe all the text in the image exactly as written, "
          "in natural reading order. Output only the transcription as plain text, with no commentary.")
lock = threading.Lock()
def call(img):
    buf = io.BytesIO(); img.save(buf, format="PNG"); b64 = base64.b64encode(buf.getvalue()).decode()
    body = json.dumps({"model": MODEL, "temperature": 0, "max_tokens": 2000, "messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}, {"type": "text", "text": PROMPT}]}]}).encode()
    for attempt in range(4):
        try:
            req = urllib.request.Request("https://api.deepinfra.com/v1/openai/chat/completions", data=body,
                                         headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            o = json.load(urllib.request.urlopen(req, timeout=300))
            return o["choices"][0]["message"]["content"] or "", o.get("usage") or {}
        except Exception as ex:
            err = repr(ex)[:200]; time.sleep(5 * (attempt + 1))
    raise RuntimeError(err)
def read(path):
    name = os.path.basename(path); d = re.search(r"_D(\d+)_", name).group(1)
    im = Image.open(path).convert("RGB"); W, H = im.size; m = 0.012; texts = []; pt = ct = 0; t0 = time.time()
    try:
        for x0, y0, x1, y1 in BLOCKS[d]:
            cr = im.crop((max(0, int((x0 - m) * W)), max(0, int((y0 - m) * H)), min(W, int((x1 + m) * W)), min(H, int((y1 + m) * H))))
            t, u = call(cr); texts.append(t.strip()); pt += u.get("prompt_tokens", 0) or 0; ct += u.get("completion_tokens", 0) or 0
    except Exception as ex:
        print("ERROR", name, ex, flush=True); return
    rec = dict(image=name, tag=TAG, model="vlm-blocks", model_version=f"{MODEL} temperature 0 per paragraph box from clean page (DeepInfra)",
               n_blocks=len(texts), text="\n".join(texts), prompt_tokens=pt, completion_tokens=ct, latency_s=round(time.time() - t0, 1), ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
    with lock:
        with open(OUT, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
done = set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)["image"])
todo = [p for p in open(LIST).read().split("\n") if p and os.path.basename(p) not in done]
print("to read", len(todo), "model", MODEL, flush=True)
with ThreadPoolExecutor(NW) as ex: list(ex.map(read, todo))
print("VLM_DONE", flush=True)

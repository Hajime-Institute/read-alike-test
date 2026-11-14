# Read-Alike Test: code and derived data

Code and derived data for the paper *Read-Alike Test: Validating Synthetic Document Degradation by Whether a Reader
Fails on the Same Words as on Real Images* (Hajime Hotta, Hajime Institute, Singapore and Ur-AI,
Japan; submitted to IJDAR).

The read-alike test asks whether a synthetic degradation makes a reader (OCR engine or vision-language model) fail on
the same words as a real degradation does, not only at the same rate. For each real degraded capture (the test
image), the generator setting is chosen on half of the words (alternating 20-word chunks, matching per-band word
accuracy down the page), and on the other half we measure Cohen's κ between the per-word read/failed vectors of the
real and the synthetic image. The yardstick is the agreement between real recaptures: the mean κ between the test
image and the other captures of the same document under the same condition. A generator passes if its κ is not
worse than this real-vs-real reference by more than the variation of the reference across documents (a
non-inferiority test with a document-level bootstrap). We apply the test to defocus blur in SmartDoc-QA smartphone
captures with four readers, and compare a downscaling generator with real 200 dpi scans in the UNLV/ISRI collection.

All code comments, docstrings and console output are in Japanese. The verdict strings stored in the JSON files are
also Japanese: 通る = pass, 決まらない = undecided, 落ちる = fail.

## What each folder holds

| Path | Contents |
|---|---|
| `code/1_fetch_data/` | `zip_range.py`, `zip_range_par.py`: fetch single members of the SmartDoc-QA zip (13.7 GB, Zenodo) with HTTP range requests. `fetch_wacc.py`: collect the per-capture Tesseract accuracy shipped with SmartDoc-QA into `results/smartdoc_wacc.json` (used to look up conditions). |
| `code/2_rectify_and_read/` | `page_box.py` (page size of a real capture, used to set the rendering dpi), `make_persp.py` (only its page-corner detection `quad` is used, by `rectify_page.py`), `rectify_page.py` (rotate a real capture by 90°, find the page corners, warp it to an A4 rectangle), `process_real.py` (rectify + Tesseract + docTR for a set of captures), and the four per-paragraph readers: `ocr_blocks.py` (Tesseract), `ocr_doctr_blocks.py` (docTR), `ocr_vision_blocks.py` (Apple Vision), `ocr_vlm_blocks.py` (Mistral-Small-3.2-24B via DeepInfra). Every reader crops the same paragraph boxes, taken from the source PDF, from real and synthetic images alike. |
| `code/3_generators/` | `make_synth.py` (tilted-page defocus `defocusplane`, uniform disk blur `defocus`, and the clean page `none`), `make_audit.py` (albumentations Defocus / GaussianBlur, Augraphy DepthSimulatedBlur), `make_lamp.py` + `gen_lamp.py` (desk-lamp capture, alone and on top of tilted-page defocus), `make_lowlight.py` (low-light generators). `degrade_lab/degrade.py` is the blur library imported by `make_synth.py` and `make_lamp.py` (see "Origin of degrade.py"). |
| `code/4_test/` | The test itself: `audit_angles.py` (one condition x one reader), with `score_words.py` (per-word read/failed vector against the ground truth), `word_xy.py`, `bootdoc.py` (document-level bootstrap). `angle_bands.py` (per-band word accuracy by capture angle). `audit_mix.py` and `run_mix.sh` (generators of known fidelity: a share p of a real capture's word outcomes replaced by null-baseline draws). |
| `code/5_aggregate/` | `reader_rule.py` (which readers are used; shared by the scripts below), `mix_summary.py` (known-fidelity counts per p), `make_facts.py` (runs every condition x reader x selection rule into `results/facts_defocus.json`), `run_lodo.py` (one setting chosen on the other documents, `results/facts_lodo.json`), `run_label.sh`, `run_label_lodo.sh`, `run_labels.py` and `label_overlap_summary.py` (overlap of illegible words), `write_tables.py` (LaTeX table rows), `make_fig_grid.py` (verdict grid figure), `sensitivity_delta.py` (δ scaled), `crosscheck_min_docs.py` (minimum number of documents per reader), `design_sensitivity.py` and `design_sensitivity_summary.py` (chunk size, number of bands, accuracy range). |
| `code/unlv/` | The UNLV/ISRI experiment: `ocr_run.py` (Tesseract per zone on real 2B/3A/3B/4B scans and on synthetic 200 dpi images made from 4B), `analyze.py` (choose a setting on half of the documents, measure κ on the other half), `split.py`, `common.py`, `score_words.py` (same as SmartDoc), `check_orientation.py` and `make_fixes.py` (one magazine page was distributed upside down). |
| `readings/` | `blocks_d1_10.json`: the paragraph boxes of SmartDoc-QA documents 1–10 as fractions of the page (identical to what `ocr_blocks.blocks()` computes from the PDFs; `ocr_vlm_blocks.py` reads it through `BLOCKS_JSON`). `readings/unlv/`: Tesseract transcriptions of the UNLV pages (`ocr_<set>_<cond>.jsonl.gz`, one record per page with per-zone text). The transcriptions of the SmartDoc-QA images are not included, because they reproduce the page text and the dataset's license does not allow re-distribution; steps 1 and 2 of the SmartDoc-QA pipeline regenerate them. |
| `results/` | `facts_defocus.json` and `facts_lodo.json` (all numbers of the SmartDoc-QA experiments; schema below), `label_overlap_ratio.json` and `label_overlap_summary.txt` (overlap of illegible words), `label_overlap/` and `label_overlap_lodo/` (per-run outputs behind it; see the README there), `paper_tables/auto_tab_*.tex` (the table rows in the paper, written by `write_tables.py`), `page_boxes.json` (output of `page_box.py`), `unlv/` (`summary_bus.json`, `summary_mag.json`, their printouts, and the orientation check and fix), `candidate_settings.json` (every generator setting that was tried, per phone and generator kind, for documents 1–10 and 11–20), `design_sensitivity/` (`facts_<variant>.json.gz` for each design value changed, `summary.txt` from `design_sensitivity_summary.py`, and `angle_bottom_minus_top_tesseract.txt` from `angle_bands.py`), `known_fidelity/` (per condition x reader outputs of `audit_mix.py`, `summary.txt` and `mix_summary.json` from `mix_summary.py`). |

No images are included (real captures, rectified pages, synthetic images, source PDFs).

### File naming

- Real capture: `(S|M)_Img_<WP|Android>_D<doc>_<L2|L3|L4>_r35_a<angle>_b<angle>[_<Ob820|Ob940|Ob1|Ob2>].jpg`
  (WP = Nokia, Android = Samsung; L2 daylight with a ceiling light, L3 night with a desk lamp, L4 desk lamp with an
  object's shadow; Ob820/Ob940 = Nokia focus steps 1/2, Ob1/Ob2 = Samsung focus steps 1/2; no suffix = in focus).
  Its rectified page is `rect_<capture name>.png`.
- Synthetic image: `syn_D<doc>_<WP|Android>_<kind>_<setting>.jpg`. `results/candidate_settings.json` lists every
  `<setting>` that was tried for each phone and kind. Generator names in `facts_*.json` map to kinds as follows: `ours_plane` = `defocusplane`
  (tilted-page defocus), `ours_uni` = `defocus` (uniform disk blur), `albDefocus`, `albGauss`, `augDepth`,
  `ours_lampdef` = `lampdef` (L3 only); for the low-light conditions `ours_plane` = `lamp`, `ours_grad` = `lightplane`,
  `ours_uni` = `lightuni`, `albBright`, `augLight`. `null_band` is the null baseline (no image). `ours_plane2`
  (`defocusplanec`, colour rendering) and `ours_var` (`defocusvar`) appear for a few conditions but are not reported
  in the paper. `syn_D<doc>_<phone>_none_0.jpg` is the clean page.

## Running the code

The scripts find each other as `<work>/code/<name>.py` and read and write `<work>/data_smartdoc/` and
`<work>/results/` (the UNLV scripts use `<work>/data_unlv/` and `<work>/results/`). The subfolders here are for
reading only; to run, copy the scripts into one flat folder of a work directory:

```sh
W=/path/to/work                     # SmartDoc-QA work directory
mkdir -p "$W/code" "$W/results" "$W/data_smartdoc"
cp code/[1-5]_*/*.py "$W/code/"
cp results/*.json "$W/results/"
# results/raw_{tess,doctr,vision,vlm}_blocks.jsonl: the SmartDoc-QA transcriptions, made by steps 1 and 2 below
LAB="$PWD/code/3_generators/degrade_lab"   # pass this as <degrade_lab>

U=/path/to/work_unlv                # UNLV work directory
mkdir -p "$U/code" "$U/results" "$U/data_unlv"
cp code/unlv/*.py "$U/code/"
cp results/unlv/orientation_fixes.json "$U/results/"
for f in readings/unlv/*.gz; do gunzip -c "$f" > "$U/results/$(basename "$f" .gz)"; done
```

Run every Python script with `python -I`. Tesseract is called as `/opt/homebrew/bin/tesseract`
(`TESS` in `ocr_blocks.py` and `unlv/common.py`); edit that line if it is installed elsewhere. `process_real.py`
expects the docTR environment at `<work>/.venv_doctr/bin/python`.

### Software versions

| Component | Version |
|---|---|
| Tesseract | 5.5.1 (leptonica 1.85.0), `-l eng --psm 6`, one call per paragraph box |
| docTR | python-doctr 1.1.0, `fast_base` + `crnn_vgg16_bn` (pretrained), torch 2.15.0, Python 3.12, Apple MPS |
| Apple Vision | via ocrmac 1.0.1, `recognition_level="accurate"`, `language_preference=["en-US"]`, macOS 26.4 (build 25E246) |
| VLM | Mistral-Small-3.2-24B-Instruct-2506 through the DeepInfra OpenAI-compatible API, temperature 0, `max_tokens` 2000 (prompt in `ocr_vlm_blocks.py`) |
| Main environment | Python 3.13, numpy 2.3.5, opencv-python 4.13.0, Pillow 10.4.0, matplotlib 3.10.8, ocrmac 1.0.1 |
| Generator environment (`make_audit.py`, `make_lowlight.py`) | Python 3.12, albumentations 2.0.8, Augraphy 8.2.6, opencv-python 5.0.0, numpy 2.5.4 |
| Poppler | `pdftoppm` / `pdftotext` 26.02.0 (rendering the source PDFs and taking paragraph boxes) |
| Test and aggregation | standard library only (`audit_angles.py` gives identical output under Python 3.9 and 3.13) |

## Getting the data

**SmartDoc-QA** (Nayef et al., 2015) is on Zenodo, record 5293201 (`Dataset SmartDoc-QA.zip`, 13.7 GB). The record
page shows CC BY 4.0, but `SmartDoc-QA_Dataset_License.pdf` inside the archive allows research use only and no
re-distribution; follow that license and cite the dataset as given in "Citation" below. The
scripts need, under `<work>/data_smartdoc/` (the zip's top folder `Dataset SmartDoc-QA/` removed):

- `Original_documents/page_1.pdf` … `page_10.pdf` and `Ground_truth/page_1.txt` … `page_10.txt`
  (enough to re-score existing transcriptions);
- `Captured_Images/{Nokia_phone,Samsung_phone}/Images/*.jpg` (only to redo rectification and reading).

Either download and unpack the whole zip, or fetch single members with `zip_range_par.py`. That needs the archive's
central directory saved as `<work>/data_smartdoc/_central_directory.bin` (the 6,001,183 bytes near the end of the
archive; an HTTP range request for the last ~6.1 MB should do, since `zip_range.py` scans for central-directory
headers, but we have not tested that route). Then:

```sh
python -I code/zip_range_par.py data_smartdoc/_central_directory.bin data_smartdoc \
  '(Original_documents/page_([1-9]|10)\.pdf|Ground_truth/page_([1-9]|10)\.txt)$'          # 20 files
python -I code/zip_range_par.py data_smartdoc/_central_directory.bin data_smartdoc \
  'Captured_Images/(Nokia|Samsung)_phone/Images/(S|M)_Img_(WP|Android)_D([1-9]|10)_L[234]_r35_a-?[0-9]+_b-?[0-9]+(_(Ob820|Ob940|Ob1|Ob2))?\.jpg$' 8   # 984 captures, 3.3 GB
python -I code/fetch_wacc.py "$W"     # optional: results/smartdoc_wacc.json
```

**UNLV/ISRI** document collection (Rice, Jenkins and Nartker, 1995, ISRI technical report TR-95-04): binary scans of
the same pages at 200 dpi (`2B`), 300 dpi (`3B`, and `3A` with a different binarization) and 400 dpi (`4B`), with
zone files and ground-truth text. We used the business-letter (`bus`) and magazine (`mag`) sets: `bus.2B`, `bus.3A`,
`bus.3B`, `bus.4B`, `mag.2B`, `mag.3A`, `mag.3B`, `mag.4B` (`.tar.gz` each), unpacked to
`<work_unlv>/data_unlv/<set>.<res>/` (each folder holds a `pages` list and `<sub>/<page>.<res>.{tif,uzn,txt}`).
The collection is distributed with the ISRI OCR evaluation tools in the Google Code archive project
`isri-ocr-evaluation-tools` (https://code.google.com/archive/p/isri-ocr-evaluation-tools/downloads), which releases the
images, zone files and ground truth under the Apache License 2.0.

## Pipeline (SmartDoc-QA)

Run from the work directory `$W`. The commands are the usage lines in each script's docstring.

1. **Rectify and read the real captures.** `page_box.py` measured the page size (Nokia about 208 dpi, Samsung about
   285 dpi, `results/page_boxes.json`); these are the rendering dpi of the generators.
   ```sh
   python -I code/page_box.py results/page_boxes.json <captures...>
   python -I code/process_real.py "$W" '<regex on capture file names>'    # rectify_page.py -> ocr_blocks.py -> ocr_doctr_blocks.py
   <venv>/bin/python -I code/ocr_vision_blocks.py results/raw_vision_blocks.jsonl blocks <images...>
   DEEPINFRA_API_KEY=... BLOCKS_JSON=<release>/readings/blocks_d1_10.json \
     python -I code/ocr_vlm_blocks.py results/raw_vlm_blocks.jsonl blocks <file listing image paths> 24
   ```
   The single readers are `python -I code/ocr_blocks.py <out.jsonl> <tag> <images...>` and
   `.venv_doctr/bin/python -I code/ocr_doctr_blocks.py <out.jsonl> <tag> <images...>`; the paper uses tag `blocks`.
   Rectified pages go to `results/real_rect/rect_*.png`.
2. **Make the synthetic images** from the source PDFs (grey, JPEG quality 90), then read them with the same four
   readers (same commands, tag `blocks`).
   ```sh
   python -I code/make_synth.py "$LAB" <out> <doc> <dpi> <phone> <kind> <values...>   # kind: none | defocus | defocusplane | defocusvar ...
   PHONE=Android DPI=285 GRID=dense <aug-venv>/bin/python -I code/make_audit.py <out> <doc...>   # albumentations / Augraphy
   python -I code/gen_lamp.py "$W" "$LAB" <out>                                         # runs make_lamp.py for all documents and phones
   <aug-venv>/bin/python -I code/make_lowlight.py <out> <dpi> <phone> <doc...>
   ```
   `make_synth.py ... none 0` gives the clean page that fixes the target words. The candidate settings are listed in
   `results/candidate_settings.json`.
3. **Run the test** for one condition and one reader (environment variables select the condition and the variant):
   ```sh
   PH=WP OB=Ob820 LIGHT=L2 MASK=sharp SEL=prof XDOC=0 NULL=1 POS=1 JSON_OUT=out.json \
     python -I code/audit_angles.py "$W" tessblk          # tessblk | doctrblk | visionblk | vlmblk
   ```
   `SEL=acc` chooses the setting by overall accuracy, `XDOC=lodo` chooses one setting on the other documents,
   `NULL=1` adds the null baseline, `POS=1` adds each real capture as a stand-in, `LABEL_OUT=<file>` writes the
   illegible-word counts.
4. **Aggregate.**
   ```sh
   python -I code/run_lodo.py "$W"                       # -> results/facts_lodo.json
   python -I code/make_facts.py "$W" <paper>/ja          # -> results/facts_defocus.json (136 runs); also writes the
                                                        #    table rows into <paper>/ja and <paper>/en if they exist
   zsh <release>/code/5_aggregate/run_label.sh "$W"      # -> labout/      (or: python3 -I code/run_labels.py "$W" 4 -> out/)
   zsh <release>/code/5_aggregate/run_label_lodo.sh "$W" # -> labout_lodo/
   python -I code/label_overlap_summary.py labout results/facts_defocus.json labout_lodo results/label_overlap_ratio.json
   python -I code/write_tables.py results/facts_defocus.json <outdir> en
   python code/make_fig_grid.py results/facts_defocus.json fig_grid.pdf
   python -I code/mix_summary.py results/known_fidelity results/known_fidelity/mix_summary.json
   python -I code/sensitivity_delta.py results/facts_defocus.json 0.9 1.0 1.8
   python -I code/crosscheck_min_docs.py results/facts_defocus.json
   python -I code/design_sensitivity.py "$W" results/design_sensitivity [variant ...] -P 3
   python -I code/design_sensitivity_summary.py results/design_sensitivity/facts_*.json --base results/facts_defocus.json results/facts_lodo.json
   ```
   The shell runners call `python3` and `code/audit_angles.py` relative to the work directory.

## Pipeline (UNLV)

Run from `$U`. `ocr_run.py` skips pages already in `results/ocr_<set>_<cond>.jsonl`.

```sh
# usage: ocr_run.py <set> <npages>[:cal|:eval] <cond ...>   (cond: 2B 3B 3A 4B syn_s<sigma>_t<T> grid)
python -I code/ocr_run.py bus 200 2B 4B 3B 3A      # real scans
python -I code/ocr_run.py bus 200 grid             # 16 synthetic settings (sigma x threshold), all 200 pages
python -I code/ocr_run.py mag 60 2B 4B 3B 3A
python -I code/ocr_run.py mag 60:cal grid          # calibration half only
python -I code/analyze.py mag 60                   # prints CHOSEN while the evaluation half lacks it; then
python -I code/ocr_run.py mag 60:eval <chosen> syn_s0.0_t128
python -I code/check_orientation.py bus 200; python -I code/check_orientation.py mag 60
python -I code/make_fixes.py bus mag               # -> results/orientation_fixes.json (mag 3A page 8086_033 was upside down)
# remove that page from results/ocr_mag_3A.jsonl, then: python -I code/ocr_run.py mag 60 3A
python -I code/analyze.py bus 200; python -I code/analyze.py mag 60   # -> results/summary_bus.json, summary_mag.json
```

The paper used 200 pages of `bus` and 60 pages of `mag` (`common.sample_pages`, seed 0), split by document
(`split.py`, seed 1). With the released UNLV readings, `analyze.py bus 200` and `analyze.py mag 60` reproduce
`results/unlv/summary_bus.json` and `summary_mag.json` exactly.

## Regenerating the paper's numbers

From the SmartDoc-QA transcriptions (steps 1 and 2 above) and the ground truth (`Ground_truth/page_*.txt`):

```sh
mkdir -p "$W/tables/ja" "$W/tables/en"
python -I code/run_lodo.py "$W"                      # -> results/facts_lodo.json (run first: the tables read it)
python -I code/make_facts.py "$W" "$W/tables/ja"     # -> results/facts_defocus.json, and the table rows in tables/ja and tables/en
python -I code/write_tables.py results/facts_defocus.json tables/en en   # -> auto_tab_exp1.tex, auto_tab_verdict.tex, auto_tab_xdoc.tex
```

`write_tables.py` also reads `facts_lodo.json` and `label_overlap_ratio.json` from the folder of
`facts_defocus.json` (the latter is optional; without it the overlap column is left out). Run on the released
`results/`, it writes `results/paper_tables/*.tex` byte for byte. Re-running `audit_angles.py` with the released code
on our transcriptions reproduced the `facts_defocus.json` entries we checked (Samsung 2 L2 with Tesseract, Nokia 1 L2 with
Vision). `make_facts.py` makes 136 runs of `audit_angles.py`, about a minute each, 8 at a time.

The rules applied by `audit_angles.py` and `write_tables.py`:

- **Words.** Target words are those read correctly on the clean synthetic page and on a sharp real frontal capture of
  the same document (`MASK=sharp`). They are cut into alternating 20-word chunks: even chunks choose the generator
  setting (squared distance between the per-band word accuracies over 5 bands down the page), odd chunks measure κ.
- **Reference and difference.** For each test image, the reference is the mean κ between the test image and the other
  captures of its group (same document, phone, focus step and lighting). The quantity tested is the mean over test
  images of (synthetic κ − reference κ).
- **Verdict.** Pass if the lower end of the document-level bootstrap 95% interval of that difference (2,000
  resamples, percentile) is above −δ; fail if the upper end is below −δ; otherwise undecided. δ is the standard
  deviation across documents of the per-document mean reference κ (generator results are not used to set it).
- **Qualified readers.** A test image is used for a reader only if the reader's word accuracy on the evaluation words
  is between 3% and 97%. A reader is considered under a condition only with at least 4 such test images from at least
  5 documents, and used (qualified) only if the null baseline fails with it under that condition
  (`code/5_aggregate/reader_rule.py`; `NULL_RULE=combined` reproduces the earlier rule, which kept every reader and
  recorded passes as undecided where the combined null baseline did not fail). Qualified readers are combined per
  condition: pass if every qualified reader passes, fail if any fails, otherwise undecided. A condition without a
  qualified reader gets no verdict. In the paper's data, Vision and Mistral never qualify.
- **Null baseline.** `null_band` drops the evaluation words at random with the test image's own per-band accuracy
  (200 draws; seed `zlib.crc32(f"{doc}|{angle}")`). It decides which readers qualify.

## Schema of `results/facts_defocus.json`

```
{
  "per_capture":                    { "<cell>|<reader>": record },   # setting chosen per test image (proposed rule)
  "per_capture_select_by_accuracy": { "<cell>|<reader>": record },   # setting chosen by overall accuracy (SEL=acc)
  "cross_document":                 { "<cell>|<reader>": record },   # one setting from documents 1-5, tested on 6-10 (3 cells)
  "per_capture_docs_6_10":          { "<cell>|<reader>": record },   # per_capture restricted to documents 6-10 (3 cells)
  "cells":   ["Nokia 1 L2", ..., "Samsung 2 L4", "Nokia low light", "Samsung low light"],
  "readers": ["Tesseract", "docTR", "Vision", "Mistral"],
  "family":  { "<cell>": "defocus" | "lowlight" },
  "null_seed": "<note on the null-baseline seed>"
}

record = {
  "rule": "equiv", "light": "L2", "sel": "prof", "reader": "tessblk", "phone": "WP", "setting": "Ob820",
  "xdoc": "0", "mask": "sharp",
  "n_captures": 39,                          # usable test images
  "n_docs": 9,                               # documents they come from
  "ceiling": { "mean": 0.455, "ci": [lo, hi] },   # reference: real-vs-real κ, document bootstrap 95% CI
  "delta": 0.148,                            # δ
  "gens": {
    "<generator>": {
      "n": 39,
      "kappa":    { "mean": 0.443, "ci": [lo, hi] },  # κ between real and synthetic
      "abs_dacc": 0.032,                             # mean |word accuracy difference| on the evaluation words
      "diff":     { "mean": -0.012, "ci": [lo, hi] },  # synthetic κ - reference κ
      "verdict":  "通る" | "決まらない" | "落ちる",     # pass | undecided | fail (per reader, before the null-baseline rule)
      "chosen":   null | "<setting>"                 # the single setting, for cross_document
    }, ...
  },
  "roles": {                                 # per_capture only: each real capture of the group used as the generator
    "M_a-10_b-5": { "n": 31, "diff": { "mean": 0.044, "ci": [lo, hi] }, "verdict": "通る" }, ...
  }
}
```

A reader with no usable test image under a cell has a record with only `n_captures: 0`, `n_docs: 0` and the
condition fields. `results/facts_lodo.json` maps `"<cell>|<reader>"` to records of the same shape for the 12 defocus
cells with `xdoc: "lodo"` (one setting chosen on the other documents, the "set on other documents" rows). The verdicts
in the paper apply the reader rule and the null-baseline rule above on top of these per-reader verdicts
(`write_tables.py`).

## Second document set (Section 5.4)

The controls were repeated, with every design value unchanged, on SmartDoc-QA documents 11 to 20 (old business
letters from the Tobacco collection). These documents come without source PDFs, so the rectified
in-focus frontal capture (`S_Img_<phone>_D<d>_L2_r35_a0_b0`) serves as the clean image and gives the paragraph boxes.

- `code/6_second_set/`: `blocks_from_sharp.py` (paragraph boxes from the in-focus capture, Tesseract psm 3 blocks),
  `gen_letters.py` (tilted-page defocus made from the in-focus capture, with the candidate settings of the main set),
  `run_letters.sh` and `run_letters_synth.sh` (rectify, read with Tesseract, docTR and Vision, run the test for
  12 conditions x 3 readers), `letters_summary.py` (counts with the paper's rules). `ocr_blocks.py`,
  `ocr_doctr_blocks.py` and `audit_angles.py` here replace the main ones in the flat work directory; they fall back to
  the in-focus capture only when a document has no source PDF and behave identically otherwise. Set `PY` and `PD` to
  the Python environments (OpenCV/ocrmac and docTR).
- `results/second_set/`: per-run verdict JSON (`audit_gen/`), the merged `facts_letters.json`, `summary.txt` (output of
  `letters_summary.py`), and `blocks_sharp.json`.
- The transcriptions of documents 11 to 20 are not included, for the same reason as for documents 1 to 10;
  `run_letters.sh` and `run_letters_synth.sh` regenerate them.

Result: 18 qualified combinations of condition and reader (no qualified reader under Nokia 1 L2 and L4); real captures
40 pass / 13 undecided / 0 fail of 53 (0 fails of 96 per qualified reader); tilted-page defocus 2 / 6 / 2 over the 10
conditions with a qualified reader.

## Origin of `degrade.py`

`code/3_generators/degrade_lab/degrade.py` is trimmed from the authors' internal degradation toolkit
(`degrade_lab`) to the capture blurs this work uses (`f_defocus`, `f_defocus_plane`, `f_defocus_var`,
`f_motion`, `f_motion_curve`) and their helpers. These functions are unchanged and give identical outputs.

## Citation

```bibtex
@article{hotta2026readalike,
  author  = {Hotta, Hajime},
  title   = {Read-Alike Test: Validating Synthetic Document Degradation by Whether a Reader Fails on the Same Words as on Real Images},
  journal = {International Journal on Document Analysis and Recognition (IJDAR)},
  year    = {2026},
  note    = {Under review}
}
```

Please also cite the datasets:

```bibtex
@inproceedings{smartdocqa2015,
  author    = {Nayef, Nibal and Luqman, Muhammad Muzzamil and Prum, Sophea and Eskenazi, S{\'e}bastien and Chazalon, Joseph and Ogier, Jean-Marc},
  title     = {{SmartDoc-QA}: A Dataset for Quality Assessment of Smartphone Captured Document Images -- Single and Multiple Distortions},
  booktitle = {2015 13th International Conference on Document Analysis and Recognition (ICDAR), 6th International Workshop on Camera-Based Document Analysis and Recognition (CBDAR)},
  pages     = {1231--1235},
  year      = {2015},
  doi       = {10.1109/ICDAR.2015.7333960}
}

@techreport{rice1995fourth,
  author      = {Rice, Stephen V. and Jenkins, Frank R. and Nartker, Thomas A.},
  title       = {The Fourth Annual Test of {OCR} Accuracy},
  institution = {Information Science Research Institute, University of Nevada, Las Vegas},
  number      = {TR-95-04},
  year        = {1995}
}
```

## License

- **Code** (`code/`): MIT License, see `LICENSE`. Copyright (c) 2026 Hajime Institute.
- **Derived data** (`readings/`, `results/`): CC BY 4.0, see `DATA_LICENSE.md`. They are derived from SmartDoc-QA
  (Nayef et al., 2015; research use only, see its license file) and from the UNLV/ISRI OCR test collection (Rice et al.,
  1995; Apache License 2.0); please attribute both. No SmartDoc-QA images, PDFs, ground truth or transcriptions are
  included.

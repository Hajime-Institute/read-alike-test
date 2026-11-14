# label_overlap and label_overlap_lodo

Overlap of illegible words: if the words a reader fails on in a synthetic image were used as the "illegible" labels,
how many of them are also illegible on the real capture. These files feed the overlap column of the verdict table
(`../paper_tables/auto_tab_verdict.tex`) through `../label_overlap_ratio.json`.

- `label_overlap/<PH>_<OB>_<LIGHT>_<reader>_<prof|acc>.jsonl.gz`: output of `code/4_test/audit_angles.py` run with
  `LABEL_OUT`, for 12 conditions x 4 readers x 2 selection rules (`prof` = per-band profile, the proposed rule;
  `acc` = overall accuracy). Produced by `code/5_aggregate/run_label.sh` (`MASK=sharp NULL=1 POS=0`).
  One line per (source, test image): `real_missed`, `src_missed`, `both` (word counts on the evaluation words; the
  recapture and null-baseline rows are weighted so that each test image counts once).
- `label_overlap_lodo/<PH>_<OB>_<LIGHT>_<reader>_lodo.jsonl.gz`: the same with one fixed setting chosen on the other
  documents (`XDOC=lodo`), produced by `code/5_aggregate/run_label_lodo.sh`.
- `*.log`: the stdout of each run (the verdict printout of `audit_angles.py`, labels in Japanese:
  通る = pass, 決まらない = undecided, 落ちる = fail).
- 8 Mistral runs in `label_overlap/` and 4 in `label_overlap_lodo/` have a `.log` but no `.jsonl`: under those
  conditions Mistral had no usable test image.
- The verdicts in these runs agree with `../facts_defocus.json` for all 464 generator/condition/reader entries.

Summary (reproduces `../label_overlap_summary.txt` and `../label_overlap_ratio.json`):

```
gunzip -k results/label_overlap/*.jsonl.gz results/label_overlap_lodo/*.jsonl.gz   # from the repository root
python -I code/5_aggregate/label_overlap_summary.py results/label_overlap results/facts_defocus.json \
    results/label_overlap_lodo results/label_overlap_ratio.json
```

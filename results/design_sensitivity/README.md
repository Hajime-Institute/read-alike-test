Design-value sensitivity (Section 5.2 of the paper). Each `facts_<variant>.json.gz` is a full rerun of `code/4_test/audit_angles.py` over the 12 defocus conditions x 4 readers x 3 selection rules (per test image by band, by word accuracy, single fixed setting) with one design value changed:

| variant | change |
|---|---|
| base | none (identical verdicts to `results/facts_defocus.json`) |
| ch10, ch40 | chunk alternating selection and evaluation words: 10 or 40 words instead of 20 |
| nosplit | selection and evaluation on the same words |
| nb3, nb10 | 3 or 10 bands instead of 5 |
| acc01, acc05, acc10 | usable test images with word accuracy 1-99%, 5-95%, or 10-90% instead of 3-97% |

`summary.txt` is the output of `code/5_aggregate/design_sensitivity_summary.py` on these files (same reader rule and null-baseline rule as the paper). `angle_bottom_minus_top_tesseract.txt` is the per-capture-angle difference between the bottom and top band accuracies (Tesseract) from `code/4_test/angle_bands.py`; the real captures that failed under other chunk sizes or accuracy ranges were all the capture tilted the opposite way (`M_a5_b10`); without the split, one frontal capture (`S_a0_b0`, Nokia 2 L2) also failed.

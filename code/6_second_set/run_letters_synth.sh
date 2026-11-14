#!/bin/zsh
# 二つ目のセットの合成画像(傾いた紙のぼけ)を三つの読み手で読み、生成器を含めて検査を回し直す(results/audit_gen)。
set -e
W=${0:A:h:h}; cd $W
PY="${PY:-python3}"   # Python with opencv, numpy and ocrmac
PD="${PD:-python3}"   # Python with python-doctr 1.1.0 and torch
S=(results/synth_letters/*.jpg)
for i in $(seq 1 400 ${#S}); do "$PY" -I code/ocr_blocks.py results/raw_tess_blocks.jsonl blocks ${S[$i,$((i+399))]} > /dev/null; done
echo TESS_SYN_DONE
for i in $(seq 1 400 ${#S}); do "$PD" -I code/ocr_doctr_blocks.py results/raw_doctr_blocks.jsonl blocks ${S[$i,$((i+399))]} > /dev/null; done
echo DOCTR_SYN_DONE
for i in $(seq 1 400 ${#S}); do "$PY" -I code/ocr_vision_blocks.py results/raw_vision_blocks.jsonl blocks ${S[$i,$((i+399))]} > /dev/null; done
echo VISION_SYN_DONE
mkdir -p results/audit_gen
for c in "WP Ob820" "WP Ob940" "Android Ob1" "Android Ob2"; do for L in L2 L3 L4; do for rd in tessblk doctrblk visionblk; do
  set -- ${=c}; o=results/audit_gen/$1_$2_${L}_${rd}.json
  [ -e $o ] || PH=$1 OB=$2 LIGHT=$L MASK=sharp XDOC=0 SEL=prof NULL=1 POS=1 JSON_OUT=$o "$PY" -I code/audit_angles.py $W $rd > results/audit_gen/$1_$2_${L}_${rd}.log 2>&1 || echo "audit failed $o"
done; done; done
echo AUDIT_GEN_DONE

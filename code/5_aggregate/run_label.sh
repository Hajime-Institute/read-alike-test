#!/bin/zsh
# 読めない語の正解としての一致を、12 条件 × 読み手 4 × 選び方 2 で書き出す。ジョブごとに別のファイルへ(同時の書き込みを避ける)
# 使い方: zsh run_label.sh <作業ディレクトリ(code/ results/ data_smartdoc/ を持つ)>  → <作業ディレクトリ>/labout/*.jsonl, *.log
B="${1:?usage: zsh run_label.sh <work dir with code/ results/ data_smartdoc/>}"; cd "$B" || exit 1; mkdir -p labout
jobs=()
for c in "WP Ob820" "WP Ob940" "Android Ob1" "Android Ob2"; do for L in L2 L3 L4; do for rd in tessblk doctrblk visionblk vlmblk; do for sel in prof acc; do
  jobs+=("$c $L $rd $sel")
done; done; done; done
printf "%s\n" "${jobs[@]}" | xargs -P 3 -L 1 sh -c 'PH=$0 OB=$1 LIGHT=$2 MASK=sharp SEL=$4 NULL=1 POS=0 LABEL_OUT=labout/$0_$1_$2_$3_$4.jsonl python3 -I code/audit_angles.py . $3 > labout/$0_$1_$2_$3_$4.log 2>&1'
echo LABEL_DONE

#!/bin/zsh
# 設定を一つに固定した場合(確かめる文書を除く文書で選ぶ。XDOC=lodo)の、読めない語の正解としての一致
# 使い方: zsh run_label_lodo.sh <作業ディレクトリ(code/ results/ data_smartdoc/ を持つ)>  → <作業ディレクトリ>/labout_lodo/*.jsonl, *.log
B="${1:?usage: zsh run_label_lodo.sh <work dir with code/ results/ data_smartdoc/>}"; cd "$B" || exit 1; mkdir -p labout_lodo
jobs=()
for c in "WP Ob820" "WP Ob940" "Android Ob1" "Android Ob2"; do for L in L2 L3 L4; do for rd in tessblk doctrblk visionblk vlmblk; do
  jobs+=("$c $L $rd")
done; done; done
printf "%s\n" "${jobs[@]}" | xargs -P 3 -L 1 sh -c 'PH=$0 OB=$1 LIGHT=$2 MASK=sharp SEL=prof XDOC=lodo NULL=0 POS=0 LABEL_OUT=labout_lodo/$0_$1_$2_$3_lodo.jsonl python3 -I code/audit_angles.py . $3 > labout_lodo/$0_$1_$2_$3_lodo.log 2>&1'
echo LODO_DONE

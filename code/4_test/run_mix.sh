#!/bin/zsh
# 忠実さの分かっている生成器(本物の撮影を割合 p だけ帰無の対照に置き換える)を、12 条件 × 読み手 4 で回す
# 使い方: zsh run_mix.sh <作業ディレクトリ(code/ results/ data_smartdoc/ を持つ)>  → <作業ディレクトリ>/out_mix/*.json, *.log
B="${1:?usage: zsh run_mix.sh <work dir with code/ results/ data_smartdoc/>}"; cd "$B" || exit 1; mkdir -p out_mix
jobs=()
for c in "WP Ob820" "WP Ob940" "Android Ob1" "Android Ob2"; do for L in L2 L3 L4; do for rd in tessblk doctrblk visionblk vlmblk; do jobs+=("$c $L $rd"); done; done; done
printf "%s\n" "${jobs[@]}" | xargs -P 6 -L 1 sh -c 'o=out_mix/$0_$1_$2_$3.json; [ -e $o ] || PH=$0 OB=$1 LIGHT=$2 MASK=sharp XDOC=0 SEL=prof NULL=1 POS=1 MIX=0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1 MIX_DRAWS=30 JSON_OUT=$o python3 -I code/audit_mix.py . $3 > out_mix/$0_$1_$2_$3.log 2>&1'
echo MIX_DONE

#!/bin/zsh
# SmartDoc-QA の文書 11–20(古い事務文書。元の PDF は無い)で、本物の撮影の対照と帰無の対照を出す。
# 手順は本文と同じ(段落ごとに読む・鮮明な撮影で読めた語に絞る・20 語ずつ交互・5 帯・3–97%・文書 5 件以上)。
# 違うのは、段落の枠と「綺麗な画像」を元の PDF ではなく、貼り直したピントの合った正面の撮影から取ること。
set -e
W=${0:A:h:h}; cd $W
PY="${PY:-python3}"   # Python with opencv, numpy and ocrmac
PD="${PD:-python3}"   # Python with python-doctr 1.1.0 and torch
# 1. 撮影を一か所に集め、貼り直す
mkdir -p imgs results/real_rect
for f in $(find direct -name "*.jpg"); do b=${f:t}; [ -e imgs/$b ] || ln -s $W/$f imgs/$b; done
todo=(); for f in imgs/*.jpg; do [ -e results/real_rect/rect_${f:t:r}.png ] || todo+=($f); done
[ ${#todo} -gt 0 ] && "$PY" -I code/rectify_page.py results/real_rect $todo > results/rectify.log
true
# 2. 段落の枠(Nokia の鮮明な撮影から。無ければ Samsung)
sh=(); for d in {11..20}; do for ph in WP Android; do f=results/real_rect/rect_S_Img_${ph}_D${d}_L2_r35_a0_b0.png; [ -e $f ] && { sh+=($f); break; }; done; done
python3 -I code/blocks_from_sharp.py results/blocks_sharp.json $sh
# 3. 三つの読み手で読む(読み済みは飛ばす)
R=(results/real_rect/rect_*.png)
"$PY" -I code/ocr_blocks.py results/raw_tess_blocks.jsonl blocks $R > /dev/null
"$PD" -I code/ocr_doctr_blocks.py results/raw_doctr_blocks.jsonl blocks $R > /dev/null
"$PY" -I code/ocr_vision_blocks.py results/raw_vision_blocks.jsonl blocks $R > /dev/null
echo READ_DONE
# 4. 検査(12 条件 × 3 読み手)。合成の候補は無いので、本物の撮影と帰無の対照だけが出る
mkdir -p results/audit
for c in "WP Ob820" "WP Ob940" "Android Ob1" "Android Ob2"; do for L in L2 L3 L4; do for rd in tessblk doctrblk visionblk; do
  set -- ${=c}; o=results/audit/$1_$2_${L}_${rd}.json
  [ -e $o ] || PH=$1 OB=$2 LIGHT=$L MASK=sharp XDOC=0 SEL=prof NULL=1 POS=1 JSON_OUT=$o "$PY" -I code/audit_angles.py $W $rd > results/audit/$1_$2_${L}_${rd}.log 2>&1 || echo "audit failed $o"
done; done; done
echo AUDIT_DONE

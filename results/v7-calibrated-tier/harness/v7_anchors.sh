#!/usr/bin/env bash
W="<harness>"
B="$W/bench"
cd "$B" || exit 9
echo "############ SEED (unfixed) ############"
python3 grade_v7.py <seed-root>/datapipe --label seed --json "$W/v7_anchor_seed.json" 2>&1 | head -5
echo
echo "############ GOLD ############"
python3 grade_v7.py "$W/ref_aa2d0a8/gold" --label gold --json "$W/v7_anchor_gold.json" 2>&1 | head -5
echo
echo "############ GOLD2 (reference) ############"
python3 grade_v7.py "$W/ref_aa2d0a8/gold2" --label gold2 --json "$W/v7_anchor_gold2.json" 2>&1 | head -5

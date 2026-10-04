#!/usr/bin/env bash
W="<harness>"
for n in 1 2 3 4 5; do
  bash "$W/prep_v241_rep.sh" "$n" | tail -2
done

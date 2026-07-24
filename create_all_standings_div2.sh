#!/usr/bin/env bash
set -e
CupYear=2026
CupDivision=2
NContests=5
Stages=($(seq 1 "$NContests"))
for i in "${Stages[@]}"; do
    folder=$((2 * i - 2 + CupDivision))
    cp -f "data/${CupYear}_vechurcup/${i}/${i}_settings_div_${CupDivision}.py" settings.py
    python3 main.py
    cp -f "created_tables/standings.pickle" "data/${CupYear}_vechurcup/standings/div${CupDivision}/${i}.pickle"
    FinalDirectory=~/Desktop/Projects/acmallukrainian/tournaments/uacup/${CupYear}/${folder}
    mkdir -p $FinalDirectory
    cp -f "created_tables/standings.html" $FinalDirectory/standings.html
done

cp -f "data/${CupYear}_vechurcup/standings/div${CupDivision}/camps_combiner_settings.py" .
python3 camps_combiner.py "${Stages[*]}"
FinalDirectory=~/Desktop/Projects/acmallukrainian/tournaments/uacup/${CupYear}/div${CupDivision}
mkdir -p $FinalDirectory
cp -f "created_tables/standings.html" $FinalDirectory/standings.html

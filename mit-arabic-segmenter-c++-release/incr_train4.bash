#/bin/bash

# for cases when we don't care about tags and stem indices, so we can use
# old dictionaries derived from system combinations (max marginal decoding) which
# discards tag and stem index information
set -e

if [ $# -lt 6 ] ;then
    echo "Usage: newfile newstem old-model1-dict old-model2-dict old-model3-dict old-model4-dict"
    exit 1
fi

newfile=$1
newstem=$2
olddict1=$3
olddict2=$4
olddict3=$5
olddict4=$6

# Trains Model 1 by initializing with dictionary
# - colon(:) seperates dictioanry filename and flags (which dictates how the dictionary will be used)
# - s = initialize stem index of words in dictionary
# - m = initialize morpheme boundaries
# - t = initialize tag
# - S = freeze stem index of words in dictionary
# - M = freeze morpheme boundaries
# - T = freeze tag

# outputs all non-completely frozen words in newfile, not just OOV words here
python2.7 run_segmenter.py -c $newfile -r 0 -i 50 -o $newstem-m1.dict -d $olddict1:mM 

# train Model 2 to 4 as per normal
# - we can specify multiple dictionaries
# - freezing and initialization policies of words gets overwritten if the same word appears in multiple places
# here,  for each model, we initialize with previous model, then overwrite non-OOV words with old dictionary

# for OOV words, we initialize with dictionary of model1 and don't freeze them
# for non-OOVs which appear in only in old data, initialize morpheme boundaries and fix them
# for non-OOVs which appear in in new data, initialize use tag from new model1 but morphmee boundaries from old dictionary (model 2)
python2.7 make_inc4_dict.py $olddict2 $newstem-m1.dict $newstem-m2-init1 $newstem-m2-init-oov $newstem-m2-init2
python2.7 run_segmenter.py -c $newfile -r 0 -i 50 -t 5 -o $newstem-m2.dict -d $newstem-m2-init-oov:sm -d $newstem-m2-init2:mM

python2.7 make_inc4_dict.py $olddict3 $newstem-m2.dict $newstem-m3-init1 $newstem-m3-init-oov $newstem-m3-init2
python2.7 run_segmenter.py -c $newfile -r 0 -i 50 -t 5 -o $newstem-m3.dict -d $newstem-m3-init-oov:smt -d $newstem-m3-init2:mtM -q

python2.7 make_inc4_dict.py $olddict4 $newstem-m3.dict $newstem-m4-init1 $newstem-m4-init-oov $newstem-m4-init2
python2.7 run_segmenter.py -c $newfile -r 0 -i 50 -t 5 -o $newstem-m4.dict -d $newstem-m4-init-oov:smt -d $newstem-m4-init2:mtM -q -a

cat <<EOF >$newstem-m1.list
$newstem-m1.dict
$olddict1
EOF
python2.7 merge_dict.py $newstem-m1.list > $newstem-merged-m1.dict

cat <<EOF >$newstem-m2.list
$newstem-m2.dict
$olddict2
EOF
python2.7 merge_dict.py $newstem-m2.list > $newstem-merged-m2.dict

cat <<EOF >$newstem-m3.list
$newstem-m3.dict
$olddict3
EOF
python2.7 merge_dict.py $newstem-m3.list > $newstem-merged-m3.dict

cat <<EOF >$newstem-m4.list
$newstem-m4.dict
$olddict4
EOF
python2.7 merge_dict.py $newstem-m4.list > $newstem-merged-m4.dict

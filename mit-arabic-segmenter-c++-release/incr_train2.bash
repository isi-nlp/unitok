#/bin/bash

set -e

if [ $# -lt 7 ] ;then
    echo "Usage: newfile newstem oldfile old-model1-dict old-model2-dict old-model3-dict old-model4-dict"
    exit 1
fi

newfile=$1
newstem=$2
oldfile=$3
olddict1=$4
olddict2=$5
olddict3=$6
olddict4=$7

# extra boundary markers will be stripped by segmenter if not removed
cat $newfile $oldfile > $newstem-merged

# Trains Model 1 by initializing with dictionary and freeze segmentations of words in it
# - colon(:) seperates dictioanry filename and flags (which dictates how the dictionary will be used)
# - sm means initialize stem index and morpheme boundaries respectively
# - S = freeze stem index of words in dictionary
# - M = freeze morpheme boundaries
# - T = freeze tag
python2.7 run_segmenter.py -c $newstem-merged -r 0 -i 50 -o $newstem-m1.dict -d $olddict1:smSMT

# train Model 2 to 4 as per normal
# now we specify more than one dictionary
# - we use old dictionary (of the same model number) for initialization and then freeze all words in it
# - for new dictionary (from preceeding model), we use it for initialization but don't freeze it
python2.7 run_segmenter.py -c $newstem-merged -r 0 -i 50 -t 5 -o $newstem-m2.dict -d $olddict2:smtSMT -d $newstem-m1.dict:sm
python2.7 run_segmenter.py -c $newstem-merged -r 0 -i 50 -t 5 -o $newstem-m3.dict -d $olddict3:smtSMT -d $newstem-m2.dict:smt -q
python2.7 run_segmenter.py -c $newstem-merged -r 0 -i 50 -t 5 -o $newstem-m4.dict -d $olddict4:smtSMT -d $newstem-m3.dict:smt -q -a


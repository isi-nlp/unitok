#/bin/bash

set -e

if [ $# -lt 4 ] ;then
    echo "Usage: newfile newstem oldfile old-model1-dict"
    exit 1
fi

newfile=$1
newstem=$2
oldfile=$3
olddict=$4

# extra boundary markers will be stripped by segmenter if not removed
cat $newfile $oldfile > $newstem-merged

# Trains Model 1 by initializing with dictionary
# - colon(:) seperates dictioanry filename and flags (which dictates how the dictionary will be used)
# - sm means initialize stem index and morpheme boundaries respectively
python2.7 run_segmenter.py -c $newstem-merged -r 0 -i 50 -o $newstem-m1.dict -d $olddict:sm

# train Model 2 to 4 as per normal
python2.7 run_segmenter.py -c $newstem-merged -r 0 -i 50 -t 5 -o $newstem-m2.dict -d $newstem-m1.dict:sm
# t means initialize tag
python2.7 run_segmenter.py -c $newstem-merged -r 0 -i 50 -t 5 -o $newstem-m3.dict -d $newstem-m2.dict:smt -q
python2.7 run_segmenter.py -c $newstem-merged -r 0 -i 50 -t 5 -o $newstem-m4.dict -d $newstem-m3.dict:smt -q -a

# So we dictionaries from Model 2 to 4 from old corpus is not used
# But you can try combining the old and new dictionaries

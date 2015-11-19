#!/bin/bash

set -e 

if [ $# -lt 3 ]; then
    echo "Usage: $0 number-of-runs infile outstem"
    exit
fi
n=$1
infile=$2
outstem=$3

d=$(dirname $0)
flist1=$outstem-m1.list
flist2=$outstem-m2.list
flist3=$outstem-m3.list
flist4=$outstem-m4.list

if [ -f $flist1 ]; then rm -f $flist1; fi
if [ -f $flist2 ]; then rm -f $flist2; fi
if [ -f $flist3 ]; then rm -f $flist3; fi
if [ -f $flist4 ]; then rm -f $flist4; fi

for r in $(seq 1 $n); do
    $d/train.bash $r $infile $outstem-r$r
    ls $outstem-r$r-m1.dict >> $flist1
    ls $outstem-r$r-m2.dict >> $flist2
    ls $outstem-r$r-m3.dict >> $flist3
    ls $outstem-r$r-m4.dict >> $flist4
done

python2.7 $d/merge_dict.py $flist1 > $outstem-m1-mmd.dict
python2.7 $d/merge_dict.py $flist2 > $outstem-m2-mmd.dict
python2.7 $d/merge_dict.py $flist3 > $outstem-m3-mmd.dict
python2.7 $d/merge_dict.py $flist4 > $outstem-m4-mmd.dict

#!/bin/bash

set -e

if [ $# -lt 3 ]; then
    echo "Usage: $0 random-seed infile outstem"
    exit
fi
r=$1 # random seed
infile=$2
outstem=$3

bindir=$(dirname $0)

noutf8="" # utf-8 DISABLED.  use: --no-utf8 otherwise

extra=${EXTRA:-""}
i=${ITERS:-50} # number of iterations
t=5 # number of POS tags
LAST=${LAST:-4} # last model

# train Model 1 (i.e. -t 1 which is the default)
cmd="python2.7 $bindir/run_segmenter.py $noutf8 -c $infile -r $r -i $i -o $outstem-m1.dict $extra"
echo $cmd;
$cmd;

if [ $LAST -gt 1 ]; then
# train Model 2 (i.e. -t 5. :sm means initialize segmentations (morphemes and stem_index) with dictionary)
    cmd="python2.7 $bindir/run_segmenter.py $noutf8 -c $infile -r $r -i $i -t $t -d $outstem-m1.dict:sm -o $outstem-m2.dict $extra"
    echo $cmd;
    $cmd;
fi
if [ $LAST -gt 2 ]; then
# train Model 3 (i.e. -t 5 -q. :smt means intialize segmentations and tags with dictionary)
    cmd="python2.7 $bindir/run_segmenter.py $noutf8 -c $infile -r $r -i $i -t $t -d $outstem-m2.dict:smt -o $outstem-m3.dict -q $extra"
    echo $cmd;
    $cmd;
    
fi

if [ $LAST -gt 3 ]; then
# train Model 4 (i.e. -t 5 -q -a)
    cmd="python2.7 $bindir/run_segmenter.py $noutf8 -c $infile -r $r -i $i -t $t -d $outstem-m3.dict:smt -o $outstem-m4.dict -q -a $extra"
    echo $cmd;
    $cmd;
fi

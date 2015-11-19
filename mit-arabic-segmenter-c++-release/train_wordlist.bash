#!/bin/bash

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 infile outdir"
    echo "trained output is in outdir/wordlist-m2.dict"
    exit 1
fi

infile=$1
tmpdir=$2
bindir=$(dirname $0)
numrestarts=25
numits=50
numtags=5
maxlen=-1  # set max length of word to segment to save memory and time

if [ ! -d $tmpdir ]; then mkdir -p $tmpdir; fi

cat $1 | cut -d ' ' -f 1 | python $bindir/convert_wordlist.py $maxlen > $tmpdir/wordlist.data

flist1=$tmpdir/wordlist-m1.list
flist2=$tmpdir/wordlist-m2.list

if [ -f $flist1 ]; then rm -f $flist1; fi
if [ -f $flist2 ]; then rm -f $flist2; fi

let n="$numrestarts-1"
for r in $(seq 0 $n); do
    outstem=$tmpdir/wordlist-model-r$r

    # train Model 1 (i.e. -t 1 which is the default)
    python2.7 $bindir/run_segmenter.py -c $tmpdir/wordlist.data -r $r -i $numits -o $outstem-m1.dict
    ls $outstem-m1.dict >> $flist1

    # train Model 2 (i.e. -t 5. :sm means initialize segmentations (morphemes and stem_index) with dictionary)
    python2.7 $bindir/run_segmenter.py -c $tmpdir/wordlist.data -r $r -i $numits  -t $numtags  -d $outstem-m1.dict:sm -o $outstem-m2.dict
    ls $outstem-m2.dict >> $flist2
done
python2.7 $bindir/merge_dict.py $flist1 > $tmpdir/wordlist-m1.dict
python2.7 $bindir/merge_dict.py $flist2 > $tmpdir/wordlist-m2.dict

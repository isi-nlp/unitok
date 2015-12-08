#!/usr/bin/env bash

set -e

SCRIPTDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

sumlog10=$SCRIPTDIR/sumlog10.pl

train=$1
test=$2
normsize=$3
tmpdir=${TMPDIR:-/tmp}
MTMP=$(mktemp -d --tmpdir=$tmpdir XXXXXX)
function cleanup() {
    rm -rf $MTMP;
}
trap cleanup EXIT

counts=$MTMP/counts
vocab=$MTMP/vocab
ngram-count -text $train -write-order 1 -write $counts
awk '$2>1' $counts | cut -f1 > $vocab
oovprob=`$SCRIPTDIR/oovprob.py -tr $train -ts $test -v $vocab`
echo $oovprob
#for order in 2 3 4 5; do
for order in 4 5; do
    lm=$MTMP/lm.$order
    ngram-count -interpolate -kndiscount -order $order -vocab $vocab -text $train -lm $lm -unk 2> /dev/null
    ngramprob=`ngram -order $order -lm $lm -unk -ppl $test -debug 2 2> /dev/null | $sumlog10 | cut -d' ' -f7 | cut -d'=' -f2`
#    ngramprob=`ngram -order $order -lm $lm -unk -ppl $test -debug 0 2> /dev/null | grep "logprob=" | head -1 | cut -d' ' -f4`
    probsum=`echo "(- $ngramprob - $oovprob)/$normsize" | bc -l`;
    ppl=`echo "e($probsum*l(2))" | bc -l`;
    echo $order $ngramprob $ppl
done
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

charorder=10

counts=$MTMP/counts

vocab=$MTMP/vocab

oovtrain=$MTMP/train.oov
oovtest=$MTMP/test.oov
oovmodel=$MTMP/model.oov
ngram-count -text $train -write-order 1 -write $counts
awk '$2>1' $counts | cut -f1 > $vocab
sed 's/ /\n/g' $train | filter.py -k $vocab -n | perl -C -lne 'print join(" ", split(""))' > $oovtrain
sed 's/ /\n/g' $test | filter.py -k $vocab -n | perl -C -lne 'print join(" ", split(""))' > $oovtest
ngram-count -order $charorder -ukndiscount -interpolate -lm $oovmodel -text $oovtrain
oovprob=`ngram -order $charorder -ppl $oovtest -lm $oovmodel -debug 2 2> /dev/null | $sumlog10 | cut -d' ' -f7 | cut -d'=' -f2`
echo $oovprob
for order in 5; do
    lm=$MTMP/lm.$order
    ngram-count -interpolate -kndiscount -order $order -vocab $vocab -text $train -lm $lm -unk 2> /dev/null

    ngramprob=`ngram -order $order -lm $lm -unk -ppl $test -debug 2 2> /dev/null | $sumlog10 | cut -d' ' -f7 | cut -d'=' -f2`
    probsum=`echo "(- $ngramprob - $oovprob)/$normsize" | bc -l`;
    ppl=`echo "e($probsum*l(2))" | bc -l`;
    echo $order $ngramprob $ppl
done
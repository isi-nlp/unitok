#!/usr/bin/env bash

#set -e

SCRIPTDIR=`dirname "$(readlink -f "$0")"`;
SCRIPTNAME=`basename $0`;
WORKDIR=`mktemp -d -t XXXXXX.$SCRIPTNAME`;
echo $WORKDIR;
trap "rm -rf $WORKDIR" EXIT

sed 's/[0-9]/@/g' $1 > $WORKDIR/digsub;
# g = map digits to @ (we don't include -p so we are doing punc sub
$SCRIPTDIR/sent2ms.py -g -x 50 -i $WORKDIR/digsub -o $WORKDIR/ms;
# extra --classes 
LAST=2 ITERS=50 EXTRA="--classes" $SCRIPTDIR/../mit-arabic-segmenter-c++-release/train.bash $RANDOM $WORKDIR/ms $WORKDIR/base;
sed 's/ /\n/g' $WORKDIR/digsub | sort | uniq -c | sort -k1nr > $WORKDIR/voc.count;
paste -d ' ' $WORKDIR/voc.count <(awk '{print $2}' $WORKDIR/voc.count | $SCRIPTDIR/uniclass.py ) > $WORKDIR/voc.count.class;
join -1 2 -2 1 <(LANG=C sort -k2 $WORKDIR/voc.count.class) <(LANG=C sort $WORKDIR/base-m2.dict) > $WORKDIR/dict.bycount;
cut -d' ' -f1,2,4,7- $WORKDIR/dict.bycount  | python $SCRIPTDIR/learnpattern.py -k -o $2;

#!/usr/bin/env bash
set -e

if hash greadlink 2> /dev/null; then
    READLINK=greadlink
else
    READLINK=readlink
fi
SCRIPTDIR=`dirname "$($READLINK -f "$0")"`;
SCRIPTNAME=`basename $0`;
WORKDIR=`mktemp -d -t XXXXXX.$SCRIPTNAME`;
#echo $WORKDIR;
trap "rm -rf $WORKDIR" EXIT

# given a corpus, clean it, find the words ending in period and the words not ending in period, calculate statistics about them.

INFILE=${1:-/dev/stdin};
OUTFILE=/dev/stdout;

CLEANFILE=$WORKDIR/cleaned
PERIODVOCAB=$WORKDIR/periodvocab
VOCAB=$WORKDIR/vocab

# clean input
tr -cd '\11\12\15\40-\176' < $INFILE > $CLEANFILE;
# period terminal vocab with non-period variant out front
sed 's/ /\n/g' < $CLEANFILE | grep "\.$" | LANG=C sort | uniq -c | awk '{print substr($2,0,length($2)-1),$2,$1}' | awk 'NF==3{print}' | LANG=C sort -k1 > $PERIODVOCAB;
# all vocab
sed 's/ /\n/g' < $CLEANFILE | sort | uniq -c | awk '{print $2,$1}' | awk 'NF==2{print}' | LANG=C sort -k1 > $VOCAB;
# period ender, its count, version without period's count, delta, ratio
LANG=C join -o 2.2,2.3,1.2 -j 1 $VOCAB $PERIODVOCAB | awk '{print $1,$2,$3,$2-$3, (($2+0.0)/($3+0.0))}' > $OUTFILE;
# same as above but for versions with no period ender, so fake the stats
LANG=C join -e 0 -o 2.2,2.3,2.9 -j 1 -v 2 $VOCAB $PERIODVOCAB | awk '{print $1,$2,$3,$2-$3, (($2+0.0)/($3+1.0))}' >> $OUTFILE;


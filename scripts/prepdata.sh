#!/usr/bin/env bash
set -e
SCRIPTDIR=`dirname "$(readlink -f "$0")"`;
SCRIPTNAME=`basename $0`;

# prepare annotation data as bio. pretty brittle. converted from oneliner.
# assumes you're in a directory with files that start with $LANGUAGE

LANGUAGE=$1;

rm -rf $LANGUAGE; 
mkdir -p $LANGUAGE; 
for ann in $LANGUAGE"_"*.ann; do 
    orig=`echo "$ann" | sed 's/\..*$//'`; 
    cat "$ann" >> $LANGUAGE/ann; 
    cat "$orig" >> $LANGUAGE/orig; 
done; 
cmd="$SCRIPTDIR/clean.py -i $LANGUAGE/orig -o $LANGUAGE/clean";
echo $cmd;
`$cmd`;
cmd="$SCRIPTDIR/clean.py -i $LANGUAGE/ann -o $LANGUAGE/tok";
echo $cmd;
`$cmd`;
cmd="$SCRIPTDIR/getseguntok.py -r $LANGUAGE/clean -t $LANGUAGE/tok -o $LANGUAGE/untok"; 
echo $cmd;
`$cmd`;
cmd="$SCRIPTDIR/train2bio.py -u $LANGUAGE/untok -t $LANGUAGE/tok -o $LANGUAGE/bio";
echo $cmd;
`$cmd`;
paste $LANGUAGE/untok $LANGUAGE/bio > $LANGUAGE/untok.bio; 
cmd="makefolds.py -i $LANGUAGE/untok.bio -f 10 -r $LANGUAGE/train/data. -e $LANGUAGE/test/data.";
echo $cmd;
`$cmd`; 
for fold in `seq 0 9`; do 
    for bin in train test; do 
	cut -f1 $LANGUAGE/$bin/data.$fold > $LANGUAGE/$bin/untok.$fold; 
	cut -f2 $LANGUAGE/$bin/data.$fold > $LANGUAGE/$bin/bio.$fold; 
	$SCRIPTDIR/bio2tok.py -u $LANGUAGE/$bin/untok.$fold -b $LANGUAGE/$bin/bio.$fold -o $LANGUAGE/$bin/tok.$fold;
    done; 
done;
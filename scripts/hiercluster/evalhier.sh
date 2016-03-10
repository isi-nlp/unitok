#!/usr/bin/env bash

set -e

SCRIPTDIR=`dirname "$(greadlink -f "$0")"`;
SCRIPTNAME=`basename $0`;
WORKDIR=`mktemp -d -t XXXXXX.$SCRIPTNAME`;
#echo $WORKDIR;
trap "rm -rf $WORKDIR" EXIT

UNISCRIPTDIR=$SCRIPTDIR/uniscripts

# just the last part of eval hier
# TODO: allow direct probing of the trained model to make this easier!!


MODEL=$1
TESTUNTOK=$4
TESTTOK=$5

BIO2AD=$UNISCRIPTDIR/bio2ad.py
LABELFROMANN=$SCRIPTDIR/labelmodelfromann.py
CLUSTEREVAL=$SCRIPTDIR/evalhierkmeanscluster.py
CONVERTLABELS=$SCRIPTDIR/convertlabels.py
AD2BIO=$SCRIPTDIR/ad2bio.py
BIOSN2TOK=$UNISCRIPTDIR/biosn2tok.py
LEV=$UNISCRIPTDIR/lev.py

TRAINAD=$WORKDIR/trainad
CLUSTERLABELS=$WORKDIR/cllabels
TESTCLUSTERS=$WORKDIR/testclusters
TESTLABELS=$WORKDIR/testlabels
TESTBIO=$WORKDIR/testbio
TESTHYP=$WORKDIR/testhyp
# convert untok + bio into ad format
# python ../unitok/scripts/bio2ad.py -i ../unitok/crf/redobio/english/train/bio.0 -o eng.ad.train.0
$BIO2AD -i $TRAINBIO -o $TRAINAD
# use ad format to label clusters
# scripts/labelmodelfromann.py -m 50k.5p.5f.2x10.u.model -i eng.untok.train.0 -g eng.ad.train.0 -o 50k.5p.5f.2x10.u.hl0.model -a 50k.5p.5f.2x10.u.hl0.95.ann -t 0.95
$LABELFROMANN -m $MODEL -i $TRAINUNTOK -g $TRAINAD -a $CLUSTERLABELS -t 0.95
# evaluate test file
# scripts/evalhierkmeanscluster.py -i eng.untok.train.0 -m 50k.5p.5f.2x10.u.hl0.model -o eng.untok.train.0.50k.tont.label
$CLUSTEREVAL -i $TESTUNTOK -m $MODEL -o $TESTCLUSTERS
# convert cluster ids to labeled clusters
# scripts/convertlabels.py -i eng.untok.train.0.50k.tont.label -a 50k.5p.5f.2x10.u.hl0.ann -o eng.untok.train.0.50k.tont.label.ann
$CONVERTLABELS -i $TESTCLUSTERS -a $CLUSTERLABELS -o $TESTLABELS
# convert labeled clusters to BIO notation
# scripts/ad2bio.py -i eng.untok.train.0 -a eng.untok.train.0.50k.tont.label.ann -o eng.untok.train.0.50k.tont.bio
$AD2BIO -i $TESTUNTOK -a $TESTLABELS -o $TESTBIO
# convert BIO to tokenization
# ../unitok/scripts/biosn2tok.py -i eng.untok.train.0 -m eng.untok.train.0.50k.tont.bio -j -t eng.untok.train.0.50k.tont.tok
$BIOSN2TOK -i $TESTUNTOK -m $TESTBIO -j -t $TESTHYP
# evaluate lev
# ../unitok/scripts/lev.py -r ../unitok/crf/redobio/english/train/tok.0 -p eng.untok.train.0.50k.tont.tok
$LEV -r $TESTTOK -p $TESTHYP

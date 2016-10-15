#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
import unicodedata as ud
import Levenshtein as lev
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="Levenshtein distance-based scoring function for use with gold tokenizations. Report raw distance, per-segment average, per-punc average",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--reffile", "-r", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input reference file")
  parser.add_argument("--hypfile", "-p", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input hypothesis file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  reffile = gzip.open(args.reffile.name, 'r') if args.reffile.name.endswith(".gz") else args.reffile
  reffile = reader(reffile)

  hypfile = gzip.open(args.hypfile.name, 'r') if args.hypfile.name.endswith(".gz") else args.hypfile
  hypfile = reader(hypfile)

  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)
  stderr = writer(sys.stderr)

  levtotal=0.0
  punctotal=0
  senttotal=0
  for refline, hypline in izip(reffile, hypfile):
    # warn/skip if character streams not the same
    # quote thing is workaround for cdectok eval
    refline = refline.strip().replace(u'“', u'"').replace(u'”', u'"')
    hypline = hypline.strip().replace(u'“', u'"').replace(u'”', u'"')


    if "".join(refline.split()) != "".join(hypline.split()):
      stderr.write("Warning: mismatched lines %s and %s. Skipping\n" % (refline, hypline))
      continue
    senttotal+=1
    # get punc count
    punctotal += len(filter(lambda x: x.startswith("P"), map(ud.category, list(refline))))
    # get lev
    levtotal += lev.distance(refline, hypline)

  outfile.write("Total distance %f\n" % levtotal)
  outfile.write("Per-line average %f\n" % (levtotal/senttotal))
  outfile.write("Per-punc average %f\n" % (levtotal/punctotal))

if __name__ == '__main__':
  main()


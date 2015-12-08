#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
import unicodedata as ud
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="replace (non-space) characters with unicode category.",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = gzip.open(args.infile.name, 'r') if args.infile.name.endswith(".gz") else args.infile
  infile = reader(infile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)


  for line in infile:
    toks = []
    for tok in line.strip().split():
      toks.append(".".join(map(ud.category, tok)))
      #outfile.write("%s %s\n" % ( tok, toks[-1]))
    outfile.write(' '.join(toks)+"\n")

if __name__ == '__main__':
  main()

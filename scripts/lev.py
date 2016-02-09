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
import Levenshtein as lev
import difflib
scriptdir = os.path.dirname(os.path.abspath(__file__))

seqmatch = difflib.SequenceMatcher()
differ = difflib.Differ()

def main():
  parser = argparse.ArgumentParser(description="Levenshtein distance-based scoring function for use with gold tokenizations. Report raw distance, per-segment average, per-punc average",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--reffile", "-r", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input reference file")
  parser.add_argument("--hypfile", "-p", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input hypothesis file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--verbose", "-v", action='store_true', default=False, help="output per-line difference along with lines")



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


  levtotal=0.0
  punctotal=0
  chartotal=0
  senttotal=0
  for refline, hypline in izip(reffile, hypfile):
    # warn/skip if character streams not the same
    refline = refline.strip()
    hypline = hypline.strip()
    # cdec workaround: all curly quotes become straight

    if "".join(refline.split()) != "".join(hypline.split()):
      sys.stderr.write("Warning: mismatched lines %s and %s. Skipping\n" % (refline, hypline))
      continue
    senttotal+=1
    # get punc count
    punctotal += len(filter(lambda x: x.startswith("P"), map(ud.category, list(refline))))
    # get char total
    chartotal += len("".join(list(refline.split())))
    # get lev
    sentdist= lev.distance(refline, hypline)
    levtotal += sentdist
    if args.verbose and sentdist > 0:
      diffres = list(differ.compare([hypline+"\n",], [refline+"\n",]))
      outfile.write("%f\n%s\n" % (sentdist, ''.join(diffres)))
      #outfile.write("%f\t%s\t%s\n" % (sentdist, refline, hypline))

  outfile.write("Total distance %f\n" % levtotal)
  outfile.write("Per-line average %f\n" % (levtotal/senttotal))
  outfile.write("Per-punc average %f\n" % (levtotal/punctotal))
  outfile.write("Per-char average %f\n" % (levtotal/chartotal))

if __name__ == '__main__':
  main()


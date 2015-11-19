#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
import numpy as np
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="Intrinsic type count-based numerical evaluation of tokenization",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--basefile", "-b", type=argparse.FileType('rb'), default=sys.stdin, help="untokenized file")
  parser.add_argument("--hypfile", "-p", type=argparse.FileType('rb'), default=sys.stdin, help="tokenized file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  basefile = args.basefile
  basefile = gzip.open(basefile.name, 'r') if basefile.name.endswith(".gz") else basefile
  basefile = reader(basefile)

  hypfile = args.hypfile
  hypfile = gzip.open(hypfile.name, 'r') if hypfile.name.endswith(".gz") else hypfile
  hypfile = reader(hypfile)

  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)

  basevoc = dd(int)
  hypvoc = dd(int)
  for line in basefile:
    for word in line.strip().split():
      basevoc[word]+=1
  for line in hypfile:
    for word in line.strip().split():
      hypvoc[word]+=1

  basetypes = set(basevoc.keys())
  hyptypes = set(hypvoc.keys())
  # average and max count of types that disappeared
  distypes = basetypes.difference(hyptypes)
  discounts = [basevoc[x] for x in distypes]
  outfile.write("%f average and %d max count of %d disappeared types (lower is better)\n" % (np.mean(discounts), max(discounts), len(discounts)))
  # average and max count and length of types that appeared
  newtypes = hyptypes.difference(basetypes)
  newcounts = [hypvoc[x] for x in newtypes]
  newlens = [len(x) for x in newtypes]
  outfile.write("%f average and %d max count of %d new types (lower is better?)\n" % (np.mean(newcounts), max(newcounts), len(newcounts)))
  outfile.write("%f average and %d max length of %d new types (lower is better?)\n" % (np.mean(newlens), max(newlens), len(newlens)))
  # average and max change of types that changed
  isectypes = basetypes.intersection(hyptypes)
  changes = np.array([hypvoc[x]-basevoc[x] for x in isectypes])
  nzchanges = changes[np.nonzero(changes)]
  outfile.write("%f average and %d max change of %d types of %d that changed (what is better?)\n" % (np.mean(nzchanges), max(nzchanges), len(nzchanges), len(changes)))

  # pct 1-count before and after, pct orig words destroyed, pct of new words created

  old1counttypes = filter(lambda x: basevoc[x] ==1, basetypes)
  new1counttypes = filter(lambda x: hypvoc[x] ==1, hyptypes)
  outfile.write("%f 1counts -> %f; %f pct destroyed, %f pct created\n" % ((len(old1counttypes)+0.0)/len(basetypes),                                                                          (len(new1counttypes)+0.0)/len(hyptypes),                                                                          (len(distypes)+0.0)/len(basetypes),                                                                          (len(newtypes)+0.0)/len(hyptypes)))
if __name__ == '__main__':
  main()

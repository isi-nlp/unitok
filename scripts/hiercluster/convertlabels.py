#!/usr/bin/env python3
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code) if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret



def main():
  parser = argparse.ArgumentParser(description="Apply semantic labels to cluster ids",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--infield", "-I", type=int, default=2, help="0-based field with cluster ids in infile")
  parser.add_argument("--annfile", "-a", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="annotation file")
  parser.add_argument("--annfield", "-A", type=int, default=0, help="0-based field with cluster ids in annfile")
  parser.add_argument("--labelfield", "-l", type=int, default=1, help="0-based field with semantic labels in annfile")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file (cluster ids replaced with semantic labels)")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  annfile = prepfile(args.annfile, 'r')
  outfile = prepfile(args.outfile, 'w')

  # TODO: use tries or something to be more efficient
  anns = {}
  for line in annfile:
    line = line.strip().split('\t')
    anns[line[args.annfield]]=line[args.labelfield]
  for line in infile:
    line = line.strip().split('\t')
    label = None
    cluster = line[args.infield]
    for key in anns.keys():
      if cluster.startswith(key):
        label = anns[key]
        break
    if label is not None:
      line[args.infield]=label
    outfile.write('\t'.join(line)+"\n")

if __name__ == '__main__':
  main()


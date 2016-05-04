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
import unicodedata as ud
from itertools import chain, combinations
scriptdir = os.path.dirname(os.path.abspath(__file__))

# https://docs.python.org/2/library/itertools.html
def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
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
  parser = argparse.ArgumentParser(description="given output of k-best carmel, restore original data by stripping double quotes from words and unescaping escaped double quotes",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')

  for line in infile:
    oldtoks = line.strip().split()
    toks = []
    for tok in oldtoks[:-1]:
      if tok[0] != '"' or tok[-1] != '"':
        sys.stderr.write("Weird: "+tok+"\n")
        sys.stderr.write(line+"\n")
        sys.exit(1)
      tok = tok[1:-1]
      tok = re.sub(r'\\\"', r'"', tok)
      toks.append(tok)
    outfile.write(' '.join(toks)+"\n")

if __name__ == '__main__':
  main()


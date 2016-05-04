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
  parser = argparse.ArgumentParser(description="given lines of data, spit out space-separated versions of that data and a character detokenizer",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output data file")
  parser.add_argument("--detokfile", "-d", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output detokenizer file")


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')
  detokfile = prepfile(args.detokfile, 'w')


  chars = set()
  puncs = set()
  for line in infile:
    oldtoks = list(line.strip())
    toks = []
    for tok in oldtoks:
      cat = ud.category(tok)
      if cat  == 'Zs':
        tok = '"space"'
      elif tok == '"':
        tok = '"quote"'
      else:
        tok = '"%s"' % tok
      if cat.startswith("P") or cat.startswith("S"):
        puncs.add(tok)
      else:
        chars.add(tok)
      toks.append(tok)
    outfile.write(' '.join(toks)+"\n")
  # assume spaces will only be inserted at punctuation and symbol
  detokfile.write("0\n")
  for char in chars:
    detokfile.write('(0 (0 %s %s))\n' % (char, char))
  nextid=1
  for char in puncs:
    detokfile.write('(0 (%d.0 "space" *e*) (%d.0 *e* *e*))\n' % (nextid, nextid))
    detokfile.write('(%d.0 (%d.1 %s %s))\n' % (nextid, nextid, char, char))
    detokfile.write('(%d.1 (0 "space" *e*) (0 *e* *e*))\n' % nextid)
    nextid+=1


if __name__ == '__main__':
  main()


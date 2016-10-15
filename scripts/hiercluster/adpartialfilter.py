#!/usr/bin/env python
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
  parser = argparse.ArgumentParser(description="generate ad offset markup from ad per-char markup and existing ad offset markup. useful for filtering down generalized tokenizers for subset evaluation",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--percharfile", "-p", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input per-char markup file")
  parser.add_argument("--annfile", "-a", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input offset annotation file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output offset annotation file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  percharfile = prepfile(args.percharfile, 'r')
  annfile = prepfile(args.annfile, 'r')
  outfile = prepfile(args.outfile, 'w')

  anns = dd(dict)
  filters = dd(dict)

  for line in annfile:
    ln, of, lab = line.strip().split('\t')
    anns[int(ln)][int(of)]=lab

  for ln, line in enumerate(percharfile):
    for of, lab in enumerate(line.strip().split()):
      if of in anns[ln]:
        filters[ln][of] = lab

  for ln in filters.keys():
    for of in filters[ln].keys():
      outfile.write("%d\t%d\t%s\n" % (ln, of, filters[ln][of]))

if __name__ == '__main__':
  main()


#!/usr/bin/env python3
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
import unicodedata as ud
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
  parser = argparse.ArgumentParser(description="make file of space-separated words into file of space-separated chars, handling space appropriately",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--addcharclass", "-a", action='store_true', default=False, help="insert unicode character class after each character")

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')

  for line in infile:
    line = line.strip()
    spaceseq = [ x.replace(' ', 'sp') for x in list(line) ]
    if args.addcharclass:
      catseq = map(ud.category, list(line))
      outfile.write(' '.join([' '.join(x) for x in zip(spaceseq, catseq)])+"\n")
    else:
      outfile.write(' '.join( spaceseq )+"\n")


if __name__ == '__main__':
  main()

#!/usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
from mspatterntok import classtag
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="replace classtag with word according to mspatterntok metric",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--nopuncsub", "-n", action='store_true', default=False, help="don't substitute symbol or punctuation in class")

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = args.infile
  infile = gzip.open(infile.name, 'r') if infile.name.endswith(".gz") else infile
  infile = reader(infile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)

  for line in infile:
    outfile.write(classtag(line, args.nopuncsub)+"\n")


if __name__ == '__main__':
  main()

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
import numpy as np
from sklearn.preprocessing import scale

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
  parser = argparse.ArgumentParser(description="scale attributes of an external file",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--fields", "-f", nargs='+', type=int, help="0-based fields that are subject to scale")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")

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

  numdata = dd(list)
  rawdata = []
  for line in infile:
    toks = line.strip().split('\t')
    for f in args.fields:
      numdata[f].append(float(toks[f]))
    rawdata.append(toks)

  for f in args.fields:
    numdata[f] = scale(np.array(numdata[f]))
  for ln, line in enumerate(rawdata):
    for f in args.fields:
      line[f] = str(numdata[f][ln])
    outfile.write('\t'.join(line)+"\n")

if __name__ == '__main__':
  main()

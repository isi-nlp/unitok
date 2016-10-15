#!/usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code) if fh.name.endswith(".gz") else fh
  if code.startswith('r'):
    ret = reader(fh)
  elif code.startswith('w'):
    ret = writer(fh)
  else:
    sys.stderr.write("I didn't understand code "+code+"\n")
    sys.exit(1)
  return ret

class LineMatchError(Exception):
  def __init__(self, value):
    self.value=value
  def __str__(self):
    return repr(self.value)

def main():
  parser = argparse.ArgumentParser(description="turn bio tags into AD/AA/DD/DA tags for hiercluster thing",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="bio input file (no spaces)")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output ad/dd/da/aa file (spaces)")


  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')


  for line in infile:
    chars = list(line.strip())
    ret = []
    for pos, currc in enumerate(chars):
      nextc = "X" if pos == len(chars)-1 else chars[pos+1]
      if currc == "B":
        ret.append("DA" if nextc == "I" else "DD")
      elif currc == "I":
        ret.append("AA" if nextc == "I" else "AD")
      else:
        ret.append("AA")
    outfile.write(' '.join(ret)+"\n")

if __name__ == '__main__':
  main()

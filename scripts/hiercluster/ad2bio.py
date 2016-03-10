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
  parser = argparse.ArgumentParser(description="ad offset markup to bio file",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input untok file")
  parser.add_argument("--annfile", "-a", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input annotation file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output bio file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  annfile = prepfile(args.annfile, 'r')
  outfile = prepfile(args.outfile, 'w')

  anns = dd(dict)

  for line in annfile:
    ln, of, lab = line.strip().split('\t')
    anns[int(ln)][int(of)]=lab
  for ln, line in enumerate(infile):
    bios = []
    # default = O for every space, B after spaces and at beginning
    nextbio="B"
    for of, char in enumerate(line.strip()):
      if char==' ':
        bios.append('O')
        nextbio="B"
      else:
        bios.append(nextbio)
        nextbio="I"
    for of, lab in anns[ln].items():
      #D* = B
      #*D = next is B too (if it's I)
      if lab.startswith('D'):
#        print("%d: %s -> %s" % (of, bios[of], "B"))
        bios[of]="B"
      if lab.endswith('D') and len(bios) > of+1 and bios[of+1]=="I":
#        print("%d: %s -> %s" % (of+1, bios[of+1], "B"))
        bios[of+1]="B"
    outfile.write(''.join(bios)+"\n")

if __name__ == '__main__':
  main()


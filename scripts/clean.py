#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))



# TODO
# also get rid of empty lines
# aprime='\s*'.join(list(a))
# re.match(aprime, b).start(0)
# re.match(aprime, b).end(0)
# b[7:].isspace()
# len(b[7:]) == 0

def main():
  parser = argparse.ArgumentParser(description="remove empty lines and other undesirables",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')

  infile = gzip.open(args.infile.name, 'r') if args.infile.name.endswith(".gz") else args.infile
  infile = reader(infile)


  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)


  for line in infile:
    line = line.strip()
    if line == "" or line.isspace():
      continue
    outfile.write(line+"\n")

if __name__ == '__main__':
  main()


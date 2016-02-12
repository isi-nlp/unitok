#! /usr/bin/env python3
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
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
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

# TODO
# also get rid of empty lines
# aprime='\s*'.join(list(a))
# re.match(aprime, b).start(0)
# re.match(aprime, b).end(0)
# b[7:].isspace()
# len(b[7:]) == 0


def clean(line):
  line = line.strip()
  if line == "" or line.isspace():
    return None
  return (' '.join(line.split()))

def main():
  parser = argparse.ArgumentParser(description="remove empty lines and other undesirables",
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
    line = clean(line)
    if line is None:
      continue
    outfile.write(line+"\n")

if __name__ == '__main__':
  main()


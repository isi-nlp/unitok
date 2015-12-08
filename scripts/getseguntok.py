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
  parser = argparse.ArgumentParser(description="given unsegmented, untokenized file and segmented, tokenized file, return segmented untokenized file",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--origfile", "-r", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="unseg, untok file")
  parser.add_argument("--tokfile", "-t", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="seg, tok file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output (seg, untok) file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  origfile = gzip.open(args.origfile.name, 'r') if args.origfile.name.endswith(".gz") else args.origfile
  origfile = reader(origfile)

  tokfile = gzip.open(args.tokfile.name, 'r') if args.tokfile.name.endswith(".gz") else args.tokfile
  tokfile = reader(tokfile)


  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)


  origlines = []
  for line in origfile:
    line = line.strip()
    if line == "" or line.isspace():
      continue
    origlines.append(line)
  orig = ''.join(origlines)
  for line in tokfile:
    line = line.strip()
    if line == "" or line.isspace():
      continue
    squashline = "".join(line.split())
    rex = '\s*'.join(map(re.escape, list(squashline)))
    match = re.search(rex, orig, re.UNICODE)
    if match is None:
      sys.stderr.write("Couldn't find [[[%s]]] in [[[%s]]]\n" % (line, orig[:len(line)]))
      sys.exit(1)
    prefix = orig[:match.start(0)]
    if (prefix is not None and not prefix.isspace() and prefix != ""):
      sys.stderr.write("Found %s but skipping prefix %s\n" % (line, prefix))
      sys.exit(1)
    outfile.write(orig[match.start(0):match.end(0)]+"\n")
    orig = orig[match.end(0):]
  if orig is not None and not orig.isspace() and orig != "":
    sys.stderr.write("Leftover: "+orig+"\n")
    sys.exit(1)
if __name__ == '__main__':
  main()


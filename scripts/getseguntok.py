#! /usr/bin/env python3
import argparse
import sys
import codecs
from collections import defaultdict as dd
import re
import os.path
import gzip
import clean
scriptdir = os.path.dirname(os.path.abspath(__file__))



# TODO
# also get rid of empty lines
# aprime='\s*'.join(list(a))
# re.match(aprime, b).start(0)
# re.match(aprime, b).end(0)
# b[7:].isspace()
# len(b[7:]) == 0

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
  parser = argparse.ArgumentParser(description="given unsegmented, untokenized file and segmented, tokenized file, return segmented untokenized file",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--origfile", "-r", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="unseg, untok file")
  parser.add_argument("--tokfile", "-t", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="seg, tok file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output (seg, untok) file")




  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  origfile = prepfile(args.origfile, 'r')
  tokfile = prepfile(args.tokfile, 'r')
  outfile = prepfile(args.outfile, 'o')


  origlines = []
  for line in origfile:
    line = clean.clean(line)
    if line is None:
      continue
    origlines.append(line)
  orig = ''.join(origlines)
  origlen = map(len, origlines)
  for ln, line in enumerate(tokfile, start=1):
    line = clean.clean(line)
    if line is None:
      continue
    squashline = "".join(line.split())
    rex = '\s*'.join(map(re.escape, list(squashline)))
    match = re.search(rex, orig, re.UNICODE)
    if match is None:
      sys.stderr.write("Couldn't find [[[%s]]] in [[[%s]]] at line %d\n" % (line, orig[:len(line)], ln))
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


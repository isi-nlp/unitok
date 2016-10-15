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

# TODO: make this py3 safe (as a nop)
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
  parser = argparse.ArgumentParser(description="make bio token tags for annotated data",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--untokfile", "-u", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="untokenized source file")
  parser.add_argument("--tokfile", "-t", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="tokenized source file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output bio file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  tokfile = prepfile(args.tokfile, 'r')
  untokfile = prepfile(args.untokfile, 'r')
  outfile = prepfile(args.outfile, 'w')


  for ln, (untokline, tokline) in enumerate(izip(untokfile, tokfile), start=1):
    unchars = list(untokline.strip())
    tokchars = list(tokline.strip())
    last="S"
    try:
      while (len(unchars) > 0):
        unchar = unchars.pop(0)
        tokchar = tokchars.pop(0)
        if unchar != tokchar:
          if tokchar != ' ':
            raise LineMatchError("[%s] vs [%s]" % (unchar, tokchar))
          tokchar = tokchars.pop(0)
          if unchar != tokchar:
            raise LineMatchError("[%s] vs [%s] after space" % (unchar, tokchar))
          curr="B"
        else:
          if unchar == " ":
            curr="O"
          elif last=="B" or last=="I":
            curr="I"
          else:
            curr="B"
        outfile.write(curr)
        last=curr
    except LineMatchError as e:
      sys.stderr.write("Lines don't match at line %d of %s and %s : %s and %s" % (ln, untokfile.name, tokfile.name, untokline, tokline))
      sys.stderr.write("Due to %s\n" % e.value)
      sys.exit(1)
    outfile.write("\n")

if __name__ == '__main__':
  main()

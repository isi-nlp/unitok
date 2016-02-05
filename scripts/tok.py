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
import unicodedata as ud # pip install unicodedata
scriptdir = os.path.dirname(os.path.abspath(__file__))



excluded = set([ud.lookup("TIBETAN MARK INTERSYLLABIC TSHEG"), # tshegs appear between syllables
                ud.lookup("TIBETAN MARK DELIMITER TSHEG BSTAR"),
                ])

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')

# TODO: make this py3 safe (as a nop)
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


def tokenizeoffset(data):
  ''' given a token without whitespace, return offsets for where split should happen;
      basically made for compatibility with mspatterntok '''
  ret = set()
  for offset, char in enumerate(data):
    cc = ud.category(char)
    if (cc.startswith("P") or cc.startswith("S")) and char not in excluded:
      if offset > 0:
        ret.add(offset)
      if offset+1 < len(data):
        ret.add(offset+1)
  return sorted(list(ret))

# TODO: replace tokenize with splitoninst(tokenizeoffset) per original word? to avoid code duplication
# but note offset stuff
def tokenize(data):
  toks = []
  offsets = []
  lastStart = None
  lastNW = None
  for offset, char in enumerate(data):
    cc = ud.category(char)
#    print char, offset, cc
    isWhitespace=False
    if cc.startswith("Z") or cc=="Cc":
      isWhitespace=True
#      print "Whitespace"
      if lastStart is not None:
#        print "Closing last region %d-%d" % (lastStart, lastNW)
        offsets.append("%d-%d" % (lastStart, lastNW))
        lastStart = None
        lastNW = None
    if (cc.startswith("P") or cc.startswith("S")) and char not in excluded:
#      print "Tokenizing"
      toks.append(' ')
      toks.append(char)
      toks.append(' ')
      if lastStart is not None:
#        print "Closing last region %d-%d" % (lastStart, lastNW)
        offsets.append("%d-%d" % (lastStart, lastNW))
        lastStart = None
        lastNW = None
#      print "Isolating %d-%d" % (offset, offset)
      offsets.append("%d-%d" % (offset, offset))
    else:
#      print "Appending"
      toks.append(char)
      if not isWhitespace:
        if lastStart is None:
#          print "Starting new token %d" % offset
          lastStart = offset
        lastNW = offset
  if lastStart is not None:
#    print "Finishing up and closing last region %d-%d" % (lastStart, lastNW)
    offsets.append("%d-%d" % (lastStart, lastNW))
  return ' '.join(''.join(toks).split()), offsets

def main():
  parser = argparse.ArgumentParser(description="unicode-based tokenization",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--offsetsfile", "-f", nargs='?', type=argparse.FileType('w'), default=None, help="file to write tokenization offsets (0-based space-seg start-end relative to original). default is not to write these")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))
  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')
  offsetsfile = None
  if args.offsetsfile is not None:
    offsetsfile = prepfile(args.offsetsfile, 'w')
  

  for line in infile:
    tokenization, offsets = tokenize(line)
    outfile.write(tokenization+"\n")
    if offsetsfile is not None:
      offsetsfile.write(' '.join(offsets)+"\n")

if __name__ == '__main__':
  main()

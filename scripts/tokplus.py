#!/usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
import unicodedata as ud
scriptdir = os.path.dirname(os.path.abspath(__file__))



# rule cascade:


excluded = set([ud.lookup("TIBETAN MARK INTERSYLLABIC TSHEG"), # tshegs appear between syllables
                ud.lookup("TIBETAN MARK DELIMITER TSHEG BSTAR"),
                ])

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

def splitoninst(word, pat):
  ''' given pattern (list of indices), split word up.
     abcdefg + (2, 6) => ab cdef g '''
  last=None
  ret = []
  for offset in reversed(pat):
    ret.insert(0, word[offset:last])
    last = offset
  ret.insert(0, word[:last])
  return ret


def forbidden(word):
  ''' special case prohibition against splitting '''
  return False

def tokenize(data):
  toks = []
  for tok in data.split():
    if forbidden(tok):
      toks.append(tok)
    else:
      toks.extend(splitoninst(tok, tokenizeoffset(tok)))
  return ' '.join(toks)

def main():
  parser = argparse.ArgumentParser(description="unicode-based tokenization with custom rules",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
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
    outfile.write(tokenize(line)+"\n")

if __name__ == '__main__':
  main()

#!/usr/bin/env python3
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
import unicodedata as ud
from itertools import chain, combinations
from math import floor, ceil
scriptdir = os.path.dirname(os.path.abspath(__file__))

# https://docs.python.org/2/library/itertools.html
def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

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


# U.N. -> U.N., U .N., U. N., U.N ., U . N .

def getsplits(word, maxsplits=-1, maxpos=-1):
  ''' get punctuation-based split points and return powerset of choices up to length limit'''
  codes = map(ud.category, list(word))
  choices = []
  for spot, code in enumerate(codes):
    if code.startswith("P"):
      if spot > 0:
        choices.append(spot)
      if spot+1 < len(word):
        choices.append(spot+1)
  if maxpos >= 0 and len(choices) > maxpos:
    choices = choices[:floor(maxpos/2)]+choices[-ceil(maxpos/2):]
  return filter(lambda x: maxsplits==-1 or len(x) <= maxsplits, powerset(choices))
  
def main():
  parser = argparse.ArgumentParser(description="spit out punctuation-segmented versions of words (for the purposes of ngram model construction)",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--maxsplits", "-m", type=int, default=3, help="max number of simultaneous split points. -1 means all allowed")
  parser.add_argument("--maxpos", "-M", type=int, default=6, help="max number of positions per word to consider splitting (from ends). -1 means all allowed")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')


  for line in infile:
    for tok in line.strip().split():
#      print("splitting [%s]" % tok)
      for splitset in getsplits(tok, maxsplits=args.maxsplits, maxpos=args.maxpos):
#        print(splitset)
        # corner case: singleton punctuation
        if len(splitset) == 1 and len(tok)==1 and splitset[0] == 0:
#          print("corner case")
          continue
        lastpos=0
        for split in splitset:
          if split > lastpos:
#            print(split)
#            print("\t%d:%d = [%s]\n" % (lastpos, split, tok[lastpos:split]))
            outfile.write(tok[lastpos:split]+"\n")
            lastpos=split
        if lastpos < len(tok):
#          print("end")
          outfile.write(tok[lastpos:]+"\n")
#          print("\t[%s]\n" % tok[lastpos:])


if __name__ == '__main__':
  main()


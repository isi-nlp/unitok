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

def seq2splits(seq):
  ''' given a sequence of strings, return tuple of indices where spaces would be '''
  retval = []
  tally = len(seq[0])
  for tok in seq[1:]:
    retval.append(tally)
    tally+=len(tok)
  # if len(seq) > 1:
  #   print "Input is "+' '.join(seq)
  #   print retval
  #   sys.exit(1)
  return tuple(retval)

def main():
  parser = argparse.ArgumentParser(description="given count, pattern, result, determine what to do when the pattern is seen",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file (orig count pattern result space separated (yuk)")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file (patterns and split boundaries, then exceptions")
  parser.add_argument("--bytok", "-k", action='store_true', default=False, help="decide majority by token count, instead of by type count")
  parser.add_argument("--thresh", "-t", default=20, type=int, help="Token count of exceptions to the pattern")


  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = args.infile
  infile = gzip.open(infile.name, 'r') if infile.name.endswith(".gz") else infile
  infile = reader(infile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)

  patterns = dd(lambda: dd(int)) # pattern -> split -> count (type or tok)
  exceptions = {} # possible exceptions. word -> (pattern, result)
  winners = {} # pattern -> result
  for line in infile:
    toks = line.strip().split()
    word = toks[0]
    count = int(toks[1])
    pattern = toks[2]
    result = seq2splits(toks[3:])
    inc = count if args.bytok else 1
    patterns[pattern][result]+=inc
    if count > args.thresh:
      exceptions[word] = (pattern, result)
  outfile.write("***PATTERNS***\n")
  for pattern in patterns.keys():
    winner = sorted(patterns[pattern].items(), key=lambda x: x[-1], reverse=True)[0]
    outfile.write("%s\t%s\n" % (pattern, ' '.join(map(str, winner[0])).strip()))
    winners[pattern] = winner[0]
  outfile.write("***EXCEPTIONS***\n")
  for word, (pattern, result) in exceptions.iteritems():
    if winners[pattern] != result:
      outfile.write("%s\t%s\n" % (word, ' '.join(map(str, result)).strip()))

if __name__ == '__main__':
  main()

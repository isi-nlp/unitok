#!/usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
import random
from mspatterntok import classtag
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="given tokens, search vocab for similar punctuation pattern",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--dictfile", "-d", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input dictionary: word, fullpattern, puncpattern")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = args.infile
  infile = gzip.open(infile.name, 'r') if infile.name.endswith(".gz") else infile
  infile = reader(infile)
  dictfile = args.dictfile
  dictfile = gzip.open(dictfile.name, 'r') if dictfile.name.endswith(".gz") else dictfile
  dictfile = reader(dictfile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)


  trie = dd(lambda: dd(list))

  for line in dictfile:
    word, full, punc = line.strip().split('\t')
    trie[full][punc].append(word)


  for line in infile:
    word = line.strip()
    full = classtag(word, False)
    punc = classtag(word, True)
    outfile.write('%s\t%s\t%s\n' % (word, full, punc))
    outfile.write('Other %s (%d):\n' % (punc, len(trie[full][punc])))
    for op in trie[full][punc][:10]:
      outfile.write('\t'+op+'\n')
    others = []
    for cat in trie[full]:
      if cat == punc:
        continue
      for op in trie[full][cat]:
        others.append(op)
    outfile.write('Other %s (%d categories; %d total):\n' % (full, len(trie[full]), len(others)))
    random.shuffle(others)
    for op in others[:10]:
      outfile.write('\t'+op+'\n')
    outfile.write('\n')

if __name__ == '__main__':
  main()

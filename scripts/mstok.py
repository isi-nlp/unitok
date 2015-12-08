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


def unmap(seq, orig):
  ''' given list of tokens that together represent the tokens in orig, 
  create new list with orig chars subbed back in'''
  teststr = ''.join(seq)
  if teststr == orig:
    return seq
  if len(teststr) != len(orig):
    raise ValueError("mapping mismatch: "+teststr+" vs "+orig)
  charseq = [list(x) for x in seq]
  offset = 0
  for word in charseq:
    for char in range(len(word)):
      word[char]=orig[offset]
      offset+=1
  return [''.join(x) for x in charseq]

def main():
  parser = argparse.ArgumentParser(description="Tokenize based on morphsyn(-like) tables",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--dictfile", "-d", nargs='?', type=argparse.FileType('rb'), help="dictionary file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--classes", "-c", action='store_true', default=False, help="class info in second position of dict file")
  parser.add_argument("--digitsub", "-g", action='store_true', default=False, help="dict has @ substitution for digits")


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

  tokmap = {}
  for line in dictfile:
    toks = line.strip().split()
    key = toks[0]
    remainder = 4 if args.classes else 3
    val = toks[remainder:]
    tokmap[key]=val
  for line in infile:
    retwords = []
    for word in line.strip().split():
      srchword = re.sub(r"\d", "@", word) if args.digitsub else word
      try:
        if srchword in tokmap:
          retwords.extend(unmap(tokmap[srchword], word))
        else:
          retwords.append(word)
      except ValueError as e:
        print e[:18]
        sys.exit(1)
    outfile.write(' '.join(retwords)+"\n")

if __name__ == '__main__':
  main()

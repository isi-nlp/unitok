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
import tok
scriptdir = os.path.dirname(os.path.abspath(__file__))


def simplecat(x, nopuncsub):
  ''' simple unicode category of utf8 input. first letter of class, conflating L and M '''
  sc = ud.category(x)[0]
  if sc == "M":
    return "L" 
  if nopuncsub and (sc == "P" or sc == "S"):
    return x
  return sc

def digsub(word, cls):
  ''' class-aware @-substitution '''
  wordlist = list(word)
  for x in range(len(word)):
    if cls[x] == "N":
      wordlist[x]="@"
  return ''.join(wordlist)


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

def classtag(word, nopuncsub):
  ''' get class tag sequence '''
  return ''.join(map(lambda x: simplecat(x, nopuncsub), word))

def main():
  parser = argparse.ArgumentParser(description="Tokenize based on morphsyn-learned pattern tables",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--patternfile", "-p", nargs='?', type=argparse.FileType('rb'), help="pattern file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--nopuncsub", "-n", action='store_true', default=False, help="don't substitute symbol or punctuation in class")
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

  patternfile = args.patternfile
  patternfile = gzip.open(patternfile.name, 'r') if patternfile.name.endswith(".gz") else patternfile
  patternfile = reader(patternfile)

  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)

  patternmap = {}
  exceptionmap = {}
  mode="x"
  for line in patternfile:
    if mode=="x":
      if line.strip() == "***PATTERNS***":
        mode="p"
      continue

    if mode=="p":
      line = line.strip()
      if line=="***EXCEPTIONS***":
        mode="e"
        continue
    toks = line.strip().split("\t")
    pat = toks[0]
    if len(toks) > 1:
      inst = map(int, toks[1].split(' '))
    else:
      inst = ()


    themap = patternmap if mode=="p" else exceptionmap
    themap[pat]=inst

  unk = 0
  for line in infile:
    retwords = []
    for word in line.strip().split():
      # if common after digsub, get exception, else get pattern on non-digsub.
      # if no pattern, remember this. no tok. follow instructions to split word
      classstring = classtag(word, args.nopuncsub)
      srchword = digsub(word, classstring) if args.digitsub else word
      try:
        if srchword in exceptionmap:
          inst = exceptionmap[srchword]
        elif classstring in patternmap:
          inst = patternmap[classstring]
        else:
#          inst = ()
          inst = tok.tokenizeoffset(word)
          unk+=1
        retwords.extend(splitoninst(word, inst))
      except ValueError as e:
        print e
        sys.exit(1)
    outfile.write(' '.join(retwords)+"\n")
  sys.stderr.write("%d unks\n" % unk)
if __name__ == '__main__':
  main()

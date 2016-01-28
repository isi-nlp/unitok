#!/usr/bin/env python3
import argparse
import sys
import codecs
from collections import defaultdict as dd
import re
import os.path
import gzip
import unicodedata as ud


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


class Tokenizer:
  def __init__(self, nopuncsub, digitsub, patternfile):
    self.nopuncsub = nopuncsub
    self.digitsub = digitsub
    self.patternmap = {}
    self.exceptionmap = {}
    mode="x"
    for line in patternfile:
      # when called from main, it's bytes. when called from
      # constructor as import, it's str
      # JM The above is probably not true. i was passing the name of the file, not the file handle!
      if type(line) == bytes:
        line = line.decode('utf8')
      line = line.strip()
      #print(line+" is of type "+str(type(line)))
      if mode=="x":
        if line == "***PATTERNS***":
          mode="p"
        continue

      if mode=="p":
        if line=="***EXCEPTIONS***":
          mode="e"
          continue
      toks = line.split("\t")
      pat = toks[0]
      if len(toks) > 1:
        inst = list(map(int, toks[1].split(' ')))
      else:
        inst = ()
      themap = self.patternmap if mode=="p" else self.exceptionmap
      #print(pat)
      themap[pat]=inst

  def tokenize(self, line):
    retwords = []
    for word in line.strip().split():
      # if common after digsub, get exception, else get pattern on non-digsub.
      # if no pattern, remember this. no tok. follow instructions to split word
      classstring = ''.join(list(map(lambda x: simplecat(x, self.nopuncsub), word)))
      srchword = digsub(word, classstring) if self.digitsub else word
      #print("word is "+word)
      #print("class string is "+classstring)
      #print("type of class string is "+str(type(classstring)))
      try:
        if srchword in self.exceptionmap:
          inst = self.exceptionmap[srchword]
        elif classstring in self.patternmap:
          #print("found in patternmap")
          inst = self.patternmap[classstring]
        else:
          #print("not in pattern or exception map")
          inst = ()
        retwords.extend(splitoninst(word, inst))
      except ValueError as e:
        print(e)
        sys.exit(1)
    ret = ' '.join(retwords)+"\n"
    return ret

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
  except IOError as msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = args.infile
  infile = gzip.open(infile.name, 'r') if infile.name.endswith(".gz") else infile
  #infile = reader(infile)
  patternfile = args.patternfile
  patternfile = gzip.open(patternfile.name, 'r') if patternfile.name.endswith(".gz") else patternfile
  #patternfile = reader(patternfile)


  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  #outfile = writer(outfile)
  tokenizer = Tokenizer(args.nopuncsub, args.digitsub, patternfile)
  for line in infile:
    outfile.write(tokenizer.tokenize(line))

if __name__ == '__main__':
  main()

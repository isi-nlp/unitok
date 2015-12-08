#! /usr/bin/env python
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

def main():
  parser = argparse.ArgumentParser(description="Convert data to morphsyn format",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--digitsub", "-g", action='store_true', default=False, help="map digits to @ symbol (but keep class D")
  parser.add_argument("--noclass", "-n", action='store_true', default=False, help="don't include symbol class string in third column")
  parser.add_argument("--nopuncsub", "-p", action='store_true', default=False, help="don't substitute symbol or punctuation in class")
  parser.add_argument("--maxlength", "-x", default=0, type=int, help="tokens longer than this will not be split. 0 means split all tokens")
  parser.add_argument("--boundary", "-b", default="~~MORPHSYN_BOUNDARY~~", help="boundary token. should match what is passed to run_segmenter.py")



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

  outfile.write("-1\t%s\t#\t#\n" % args.boundary)
  for line in infile:
    for word in line.strip().split():
      cat = "0" if args.maxlength > 0 and len(word) > args.maxlength else "1"
      classstring = ''.join(map(lambda x: simplecat(x, args.nopuncsub), word))
      if args.digitsub:
        word = digsub(word, classstring)
      if args.noclass:
        classstring="#"
      outfile.write("%s\t%s\t%s\t#\n" % (cat, word, classstring))
    outfile.write("-1\t~~\t#\t#\n")        


if __name__ == '__main__':
  main()

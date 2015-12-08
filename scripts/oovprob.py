#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
from math import log, exp, factorial
scriptdir = os.path.dirname(os.path.abspath(__file__))

# http://dl.acm.org/citation.cfm?id=146685
# section 3.2



def main():
  parser = argparse.ArgumentParser(description="Given a training and test corpus, as well as a vocabulary of training, score oovs in the test corpus according to a strategy by brown et al. 92",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--trainfile", "-tr", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input train file")
  parser.add_argument("--testfile", "-ts", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input test file")
  parser.add_argument("--vocabfile", "-v", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input vocabulary file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--unicodesize", default=120520, type=int, help="number of printable unicode characters. This defaults to the unicode 8.0 size, including unihan")

# 'graphic characters' from http://babelstone.blogspot.com/2005/11/how-many-unicode-characters-are-there.html
# Graphic characters are those characters with a General Category other than Cc, Cn, Co, Cs, Cf, Zl and Zp, that is to say ordinary visible characters.

  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')

  trainfile = args.trainfile
  trainfile = gzip.open(trainfile.name, 'r') if trainfile.name.endswith(".gz") else trainfile
  trainfile = reader(trainfile)

  testfile = args.testfile
  testfile = gzip.open(testfile.name, 'r') if testfile.name.endswith(".gz") else testfile
  testfile = reader(testfile)

  vocabfile = args.vocabfile
  vocabfile = gzip.open(vocabfile.name, 'r') if vocabfile.name.endswith(".gz") else vocabfile
  vocabfile = reader(vocabfile)

  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)


  #(lambda^k)/k! e^{-lambda}p^k
  # lambda = average number of characters per token in training
  # k = length of word
  # 1/p is the number of printable characters

  p = 1.0/args.unicodesize

  vocab = set()
  for line in vocabfile:
    vocab.add(line.strip())

  tokcount = 0.0
  lengthcount = 0.0
  for line in trainfile:
    for tok in line.strip().split():
      tokcount+=1
      lengthcount+=len(tok)
  lamb = lengthcount/tokcount
  eneglam = exp(-lamb)
  oovprob = 0.0
  for line in testfile:
    for tok in line.strip().split():
      if tok in vocab:
        continue
      k = len(tok)
      # avoid underflow: do it all in log space
      # to deal with large k, convert p^k to base lamb
      # so lamb^k * eneglam * p^k becomes 
      # lamb^k * lamb^z * eneglam = lamb^(k+z) * eneglam
      # where z = k log(p)/log(lamb)
      try:
        z = k * log(p) / log(lamb)
        numerator = log(lamb**(k+z) * eneglam, 2)
        contrib = (numerator - log(factorial(k), 2))
        oovprob += contrib
      except ValueError:
        print lamb, k, eneglam, p
        raise
  outfile.write("%f\n" % oovprob)


if __name__ == '__main__':
  main()

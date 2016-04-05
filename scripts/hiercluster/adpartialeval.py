#!/usr/bin/env python
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
from colorama import Fore, Back, Style # pip install colorama
scriptdir = os.path.dirname(os.path.abspath(__file__))


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



def main():
  parser = argparse.ArgumentParser(description="evaluate ad offset markup against ad per-char markup",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--reffile", "-r", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input per-char reference markup file")
  parser.add_argument("--untokfile", "-u", nargs='?', type=argparse.FileType('r'), default=None, help="input untok file. triggers debug analysis")
  parser.add_argument("--window", "-w", type=int, default=5,  help="how much context to show in debug analysis")
  parser.add_argument("--annfile", "-a", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input offset annotation file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output accuracy file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  reffile = prepfile(args.reffile, 'r')
  untokfile = prepfile(args.untokfile, 'r') if args.untokfile is not None else None
  annfile = prepfile(args.annfile, 'r')
  outfile = prepfile(args.outfile, 'w')
  window = args.window

  untoks = []
  if untokfile is not None:
    for line in untokfile:
      untoks.append(line.strip())

  anns = dd(dict)
  scores = dd(lambda: dd(float))

  toks = 0.0
  for line in annfile:
    ln, of, lab = line.strip().split('\t')
    anns[int(ln)][int(of)]=lab
    scores[lab]["GUESS"]+=1.0
    toks+=1.0
  hits = 0.0

  for ln, line in enumerate(reffile):
    for of, lab in enumerate(line.strip().split()):
      if of in anns[ln]:
        scores[lab]["GOLD"]+=1.0
        if lab == anns[ln][of]:
          hits +=1.0
          scores[lab]["HIT"]+=1.0
        elif untokfile is not None:
          prefix = untoks[ln][max(0, of-window):of]
          prefix = Fore.BLUE+'_'*(window-len(prefix))+Fore.RESET+prefix
          suffix = untoks[ln][of+1:min(len(untoks[ln]), of+window+1)].rstrip('\n')
          suffix = suffix+Fore.BLUE+'_'*(window-len(suffix))+Fore.RESET
          outfile.write("%s\t%s\t%s%s%s\n" % (anns[ln][of], lab, prefix, untoks[ln][of], suffix))

  for lab in scores.keys():
    guess = scores[lab]["GUESS"]
    hit = scores[lab]["HIT"]
    gold = scores[lab]["GOLD"]
    prec = 0.0 if guess <= 0 else hit/guess
    rec = 0.0 if gold <= 0 else hit/gold
    fm = 0.0 if prec+rec <= 0 else 2*(prec*rec)/(prec+rec)
    outfile.write("%s p %.2f r %.2f f %.2f guess %d hit %d gold %d\n" % (lab, prec, rec, fm, guess, hit, gold))
  outfile.write("Overall: %.2f %d hit %d seen\n" % (hits/toks, hits, toks))

if __name__ == '__main__':
  main()


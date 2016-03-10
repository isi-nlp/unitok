#!/usr/bin/env python3
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code) if fh.name.endswith(".gz") else fh
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
  parser = argparse.ArgumentParser(description="Given untok, unseg file and biosn markup, output seguntok, segtok, and bio files",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file (untokenized, unsegmented source)")
  parser.add_argument("--markupfile", "-m", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="bio(sn) markup file")
  parser.add_argument("--justbio", "-j", action='store_true', default=False, help="assume input is BIO (nospace) markup")
  parser.add_argument("--untokfile", "-u", nargs='?', type=argparse.FileType('w'), default=None, help="segmented, untokenized file")
  parser.add_argument("--tokfile", "-t", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="segmented, tokenized file")
  parser.add_argument("--biofile", "-b", nargs='?', type=argparse.FileType('w'), default=None, help="bio file, representing tokenization")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  markupfile = prepfile(args.markupfile, 'r')
  tokfile = prepfile(args.tokfile, 'w')
  untokfile = prepfile(args.untokfile, 'w') if args.untokfile is not None else None
  biofile = prepfile(args.biofile, 'w') if args.biofile is not None else None

  for ln, (textline, markupline) in enumerate(zip(infile, markupfile), start=1):
    chars = list(textline.strip())
    marks = markupline.strip().split()
    if len(chars) != len(marks):
      raise IndexError("input and markup don't match: line %d\n" % ln)
    lastLabel = None
    for char, mark in zip(chars, marks):
      # mark = seg+label. seg = E (delete), S(boundary), N(ignore). label = X (must go with E), B (begin), I (in), O (out)
      seg, label = mark.split('+')
      if seg == "E":
        if label != "X":
          raise TypeError("Bad annotation: %s\n" % mark)
        continue
      # label + lastlabel determine space in tokfile.
      if (label=='B' and lastLabel=='B') or (label=='B' and lastLabel=='I'):
        tokfile.write(' ')
      lastLabel=label
      # write the data to various places.
      tokfile.write(char)
      if biofile is not None:
        biofile.write(label)
      if untokfile is not None:
        untokfile.write(char)
      # decide to break line (note: this resets label)
      if seg == "S":
        lastLabel=None
        for fh in (tokfile, biofile, untokfile):
          if fh is not None:
            fh.write('\n')

if __name__ == '__main__':
  main()


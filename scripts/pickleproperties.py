#! /usr/bin/env python
import argparse
import sys
import codecs

from collections import defaultdict as dd
import re
import os.path
import gzip
import pickle
scriptdir = os.path.dirname(os.path.abspath(__file__))


def main():
  parser = argparse.ArgumentParser(description="Pickle a unicode properties file",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="unicode properties file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('wb'), default=sys.stdout, help="output pickle file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = gzip.open(args.infile.name, 'r') if args.infile.name.endswith(".gz") else args.infile
  #infile = reader(infile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  #outfile = writer(outfile)


  properties = dd(set)
  for line in infile:
    line = line[:line.find("#")].strip()
    if line == "" or line.isspace():
      continue
    coderange, codeclass = [x.strip() for x in line.split(';')]
    codes = []
    if ".." in coderange:
      scode, ecode = coderange.split("..")
      codes.extend(list(range(int(scode, 16), int(ecode, 16)+1)))
    else:
      codes.append(int(coderange, 16))
    for unichar in map(chr, codes):
      properties[codeclass].add(unichar)
  for propitem in properties.items():
    sys.stderr.write("%d entries for %s\n" % (len(propitem[1]), propitem[0]))
  pickle.dump(properties, outfile)

if __name__ == '__main__':
  main()


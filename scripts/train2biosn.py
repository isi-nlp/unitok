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


# class BioTokIterator:
#   def __init__(self, biofile, tokfile):
#     self.biolines = biofile.readlines()
#     self.toklines = tokfile.readlines()
#     if len(self.biolines) != len(self.toklines):
#       raise IndexError("tok and bio file mismatch")
#     currbioline = biolines.pop(0).strip()
#     currtokline = toklines.pop(0).strip()
#     if len(currbioline) != len(currtokline):
#       raise IndexError("tok and bio line mismatch: %s, %s\n" % (currbioline, currtokline))

#   def next(self):
#     if le

def main():
  parser = argparse.ArgumentParser(description="Given orig (unseg, untok) file, seg, tok file, and corresponding bio file, make biosn annotation file",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--unsegfile", "-s", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="untokenized, unsegmented source file")
  parser.add_argument("--untokfile", "-u", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="segmented, untokenized file")
  parser.add_argument("--biofile", "-b", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="bio file, representing tokenization")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output biosn file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  unsegfile = prepfile(args.unsegfile, 'r')
  biofile = prepfile(args.biofile, 'r')
  untokfile = prepfile(args.untokfile, 'r')
  outfile = prepfile(args.outfile, 'w')

  # re-construct line in unseg with lines from tok one char at a time, inserting characters where necessary. track these annotations.

  biolines = biofile.readlines()
  untoklines = untokfile.readlines()
  try:
    btcharzip = zip(biolines.pop(0).strip(), untoklines.pop(0).strip())
  except IndexError:
    sys.stderr.write("ran out of tok lines at untok line %d\n" % ul)
    sys.exit(1)
  cb, ct = btcharzip.__next__()
  endOfBio=False
  for ul, line in enumerate(unsegfile, start=1):
    if endOfBio:
      sys.stderr.write("Got to end of bio/untok before end of unseg\n")
      sys.exit(1)
    otoks = []
    for ch in list(line.strip()):
      if ch == ct:
        segclass="N"
        bioclass=cb
        try:
          cb, ct = btcharzip.__next__()
        except StopIteration:
          segclass="S"
          try:
            btcharzip = zip(biolines.pop(0).strip(), untoklines.pop(0).strip())
            cb, ct = btcharzip.__next__()
          except IndexError:
            endOfBio=True
      else:
        segclass="E"
        bioclass="X"
      otoks.append("%s+%s" % (segclass, bioclass))
    outfile.write(' '.join(otoks)+"\n")
    # problem if we're not out of toks
    # try:
    #   cb, ct = btcharzip.__next__()
    #   sys.stderr.write("We popped %s, %s at end of line %d\n" % (cb, ct, ul))
    #   sys.exit(1)
    # except StopIteration:
    #   pass
if __name__ == '__main__':
  main()


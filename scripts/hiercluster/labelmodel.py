#!/usr/bin/env python3
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
import unicodedata as ud
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.cluster import MiniBatchKMeans, KMeans
import collections
import itertools
import pickle
import hierkmeanscluster as hkmc
from hierkmeanscluster import ModelTree, pDBSCAN

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
  parser = argparse.ArgumentParser(description="add or modify hand labels on model file ",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--modelfile", "-m", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input model file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('wb'), default=None, help="output model file")
  parser.add_argument("--annfile", "-a", nargs='?', type=argparse.FileType('w'), default=None, help="output annotation file")
  parser.add_argument("--refine", "-r", action='store_true', default=False, help="dynamically refine")
  parser.add_argument("--debug", "-d", action='store_true', default=False, help="debug mode")


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  modelfile = prepfile(args.modelfile, 'rb')
  outfile = prepfile(args.outfile, 'wb') if args.outfile is not None else None
  annfile = prepfile(args.annfile, 'w') if args.annfile is not None else None

  fullmodel = pickle.load(modelfile)

  features, tokfeatures = hkmc.prepfeatures(fullmodel['settings'])

  values = [ ('AA', 'attach both sides (noop)'),
             ('DD', 'disconnect both sides'),
             ('AD', 'disconnect right only'),
             ('DA', 'disconnect left only'),
             ('AN', 'attach left, newline right'),
             ('DN', 'disconnect left, newline right'),
             ]
  if fullmodel['model'].handLabel(values=values, annfile=annfile, refine=args.refine):
    print("Stopping early")

  if outfile is not None:
    pickle.dump(fullmodel, outfile)

if __name__ == '__main__':
  main()


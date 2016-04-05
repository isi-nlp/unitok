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
  parser = argparse.ArgumentParser(description="add hand labels on model file given annotated data",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--modelfile", "-m", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input model file")
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input untokenized text")
  parser.add_argument("--goldfile", "-g", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input gold labels")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('wb'), default=None, help="output model file")
  parser.add_argument("--annfile", "-a", nargs='?', type=argparse.FileType('w'), default=None, help="output annotation file")
# TODO!  parser.add_argument("--refine", "-r", action='store_true', default=False, help="dynamically refine")
  parser.add_argument("--debug", "-d", action='store_true', default=False, help="debug mode")
  parser.add_argument("--thresh", "-t", type=float, default=0.75, help="how pure a class has to be")


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  modelfile = prepfile(args.modelfile, 'rb')
  infile = prepfile(args.infile, 'r')
  goldfile = prepfile(args.goldfile, 'r')
  outfile = prepfile(args.outfile, 'wb') if args.outfile is not None else None
  annfile = prepfile(args.annfile, 'w') if args.annfile is not None else None

  fullmodel = pickle.load(modelfile)

  settings = fullmodel['settings']
  features, tokfeatures = hkmc.prepfeatures(settings)

  values = [ ('AA', 'attach both sides (noop)'),
             ('DD', 'disconnect both sides'),
             ('AD', 'disconnect right only'),
             ('DA', 'disconnect left only'),
             ('AN', 'attach left, newline right'),
             ('DN', 'disconnect left, newline right'),
             ]
  data, info, datamap = hkmc.prepdata(infile, settings['possibles'], features, tokfeatures, args.debug, sparse=settings['sparse'], isTargetPunc=settings['unicodepossibles'], dv=fullmodel['feats'])
  goldlabels = []
  golddata = [ x.split() for x in [ y.strip() for y in goldfile.readlines() ] ]
  for infoblock in info:
    goldlabels.append(golddata[infoblock['ln']][infoblock['offset']])
  goldlabels = np.array(goldlabels)
  fullmodel['model'].classifydata(data, info, goldlabels, annfile, thresh=args.thresh)

  if outfile is not None:
    pickle.dump(fullmodel, outfile)

if __name__ == '__main__':
  main()


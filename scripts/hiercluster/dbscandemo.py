#!/usr/bin/env python3

# DO NOT USE TOO MUCH
# just try dbscan, print labels, single level. most args are ignored

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
import numpy as np # pip install numpy
import sklearn
from sklearn.feature_extraction import DictVectorizer # pip install sklearn
from sklearn.cluster import MiniBatchKMeans, KMeans, DBSCAN
import collections
import itertools
import pickle
import random
import copy
from collections import Counter
if int(sklearn.__version__.split('.')[0]) > 0 or int(sklearn.__version__.split('.')[1]) > 17:
  from sklearn.exceptions import NotFittedError
else:
  from sklearn.utils.validation import NotFittedError
from colorama import Fore, Back, Style # pip install colorama
import hierkmeanscluster as hkmc
from hierkmeanscluster import ModelTree


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
  parser = argparse.ArgumentParser(description="k means clustering for periods. see unitok/scripts/learntok for some inspiration",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  #parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('wb'), default=None, help="output file")
  parser.add_argument("--tontfile", "-t", nargs='?', type=argparse.FileType('w'), default=None, help="test on train output file")
  parser.add_argument("--unicodepossibles", "-u", action='store_true', default=False, help="interpret possibles list as unicode class prefixes")
  parser.add_argument("--kclusters", "-k", default=2, type=int, help="number of clusters per layer")
#  parser.add_argument("--clean", "-c", action='store_true', default=False, help="clean model training (no tont)")
  parser.add_argument("--layers", "-y", default=2, type=int, help="number of layers")
  parser.add_argument("--minclustersize", "-z", default=10.0, type=float, help="no cluster splitting below this pct of training data")
  parser.add_argument("--leftcontext", "-l", default=5, type=int, help="make features for this number of previous characters")
  parser.add_argument("--rightcontext", "-r", default=0, type=int, help="make features for this number of next characters")
  parser.add_argument("--nochar", "-n", action='store_false', dest='charfeature', default=True,  help="no character features (class only)")
  parser.add_argument("--possibles", "-p", nargs='+', default=['.'], help="set of characters to possibly split on")
  parser.add_argument("--handlabel", "-H", action='store_true', default=False, help="do hand labeling after training")
  parser.add_argument("--dbscan", action='store_true', default=False, help="try dbscan instead of kmeans")
  parser.add_argument("--debug", "-d", action='store_true', default=False, help="debug mode")
  parser.add_argument("--banned", nargs='+', default=[], help='tok-based features to remove')
  parser.add_argument("--paramnames", nargs='+', default=[], help='algorithm parameter names')
  parser.add_argument("--paramvals", nargs='+', default=[], help='algorithm parameter values')

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  tontfile = prepfile(args.tontfile, 'w') if args.tontfile is not None else None

  settings = {}
  settings['kclusters'] = args.kclusters
  settings['layers'] = args.layers
  settings['minclustersize'] = args.minclustersize
  settings['leftcontext'] = args.leftcontext
  settings['rightcontext'] = args.rightcontext
  settings['possibles'] = args.possibles
  settings['unicodepossibles'] = args.unicodepossibles
  settings['charfeature'] = args.charfeature
  settings['banned'] = args.banned

  features, tokfeatures = hkmc.prepfeatures(settings)
  

#  print("Preparing data")
  data, info, datamap = hkmc.prepdata(infile, args.possibles, features, tokfeatures, args.debug, isTargetPunc=args.unicodepossibles)

#  print("Done")
  #print(data.shape)
  if(args.debug):
    print(data)

  modeltype = MiniBatchKMeans
  modelkwargs = {'n_clusters':args.kclusters}
  if args.dbscan:
    modeltype = DBSCAN
    modelkwargs = {'eps':0.2}

  if len(args.paramnames) != 0:
    modelkwargs = dict(zip(args.paramnames, map(float, args.paramvals)))
  print(modelkwargs)
  modelTree = ModelTree(modeltype, data, info, modelkwargs=modelkwargs)

  labels = modelTree.model.fit_predict(modelTree.data)
  for label in set(labels):
    subset = modelTree.data[labels==label]
    subinfo = modelTree.info[labels==label]
    tontfile.write("%s\t%d\n" % (label, len(subinfo)))
    for elem in subinfo:
      tontfile.write("%s\t%s\t%s\n" % (label, hkmc.formatContext(elem), str(elem['feats'])))

if __name__ == '__main__':
  main()


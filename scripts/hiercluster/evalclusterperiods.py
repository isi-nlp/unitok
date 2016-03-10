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
# from sklearn.feature_extraction import DictVectorizer
# from sklearn.preprocessing import LabelEncoder
# from sklearn.cluster import KMeans
# from pystruct.models import ChainCRF
# from pystruct.learners import FrankWolfeSSVM, SubgradientSSVM
# import collections
# import itertools
import pickle
import clusterperiods

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
  parser = argparse.ArgumentParser(description="k means clustering given an established model",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input sentence file")
  parser.add_argument("--modelfile", "-m", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="pickled model file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=None, help="output format TBD file")


  # TODO: finish implementation! model parameters must get passed!

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  tontfile = prepfile(args.tontfile, 'w')


  global features
  if args.leftcontext > 0:
    for i in range(1, args.leftcontext+1):
      features['class-%d' % i] = lambda x, y, i=i: classoffset(x, y, -i)
      features['char-%d' % i] = lambda x, y, i=i: charidoffset(x, y, -i)
  if args.rightcontext > 0:
    for i in range(1, args.rightcontext+1):
      features['class+%d' % i] = lambda x, y, i=i: classoffset(x, y, i)
      features['char+%d' % i] = lambda x, y, i=i: charidoffset(x, y, i)


  
  data, info, datamap = prepdata(infile, args.possibles, args.debug)
  #print(data.shape)
  if(args.debug):
    print(data)
  km = KMeans(n_clusters=args.kclusters)

  labels = km.fit_predict(data)

  for label, inftuple in zip(labels, info):
    tontfile.write("%s\t%s\n" % (label, inftuple[0]))
  if args.outfile is not None:
    ret = {}
    ret['model'] = km
    ret['feats'] = datamap
    pickle.dump(ret, args.outfile)

if __name__ == '__main__':
  main()


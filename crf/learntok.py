#!/usr/bin/env python3
import argparse
import sys
import codecs
from collections import defaultdict as dd
import re
import os.path
import gzip
import unicodedata as ud
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import LabelEncoder
from pystruct.models import ChainCRF
from pystruct.learners import FrankWolfeSSVM
import collections
import itertools

if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip

scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  ret = gzip.open(fh.name, code) if fh.name.endswith(".gz") else fh
  if sys.version_info[0] >=3:
    return ret
  if code.startswith('r'):
    ret = reader(fh)
  elif code.startswith('w'):
    ret = writer(fh)
  else:
    sys.stderr.write("I didn't understand code "+code+"\n")
    sys.exit(1)
  return ret

def charclass(line, pos, short):
  ''' what is the character class of the character at pos. and is it shorthand or not? '''
  char = line[pos]
  cclass = ud.category(char)
  return cclass[0] if short else cclass

def currclass(line, pos):
  return charclass(line, pos, True)
def lastclass(line, pos):
  return "XS" if pos == 0 else charclass(line, pos-1, True)
def nextclass(line, pos):
  return "XE" if pos+1 == len(line) else charclass(line, pos+1, True)

# features in use
features = {'currclass': currclass,
            'lastclass': lastclass,
            'nextclass': nextclass,
           }

def featurize(line):
  ''' get a feature vector for the line '''
  ret = []
  for pos in range(len(line)):
    vec = {}
    for fname, ffun in features.items():
      vec[fname] = ffun(line, pos)
    ret.append(vec)
  return np.array(ret)


def numberize_features(dataset, unrolled_dataset):
  ''' turn non-numeric features into sparse binary features; also return the feature map '''
  # http://fastml.com/converting-categorical-data-into-numbers-with-pandas-and-scikit-learn/
  # http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.DictVectorizer.html
  dv = DictVectorizer(sparse=False) # can we make it true?
  dv = dv.fit(unrolled_dataset.flatten())
  return np.array(list(map(dv.transform, dataset))), dv

def numberize_labels(labelset, unrolled_labelset):
  ''' turn non-numeric labels into numeric space; also return the feature map '''
  # http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.LabelEncoder.html
  le = LabelEncoder()
  le = le.fit(unrolled_labelset.flatten())
  return np.array(list(map(le.transform, labelset))), le

basestring = (str, bytes)
def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def main():
  parser = argparse.ArgumentParser(description="learn to tokenize",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--untokfile", "-u", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="untok file")
  parser.add_argument("--biofile", "-b", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="bio file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  untokfile = prepfile(args.untokfile, 'r')
  biofile = prepfile(args.biofile, 'r')
  outfile = prepfile(args.outfile, 'w')

  data = []
  mapdata = []
  labels = []
  maplabels = []
  for untokline, bioline in izip(untokfile, biofile):
    feats = featurize(untokline.strip())
    data.append(feats)
    mapdata.extend(feats)
    labs = list(bioline.strip())
    labels.append(labs)
    maplabels.extend(labs)
#    print(type(np.array(data).ravel()[0]))
  data, datamap = numberize_features(np.array(data), np.array(mapdata))
  labels, labelmap = numberize_labels(np.array(labels), np.array(maplabels))

#  print(data)
#  print(labels)
  model = ChainCRF()
  ssvm = FrankWolfeSSVM(model=model, C=.1, max_iter=11)
  ssvm.fit(data, labels)
  # TONT
  print("TONT score with chain CRF: %f" % ssvm.score(data, labels))


  model = ChainCRF
if __name__ == '__main__':
  main()


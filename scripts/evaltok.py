#!/usr/bin/env python3
import argparse
import sys
import codecs
from collections import defaultdict as dd
import re
import os.path
import gzip
# import unicodedata as ud
import numpy as np
# from sklearn.feature_extraction import DictVectorizer
# from sklearn.preprocessing import LabelEncoder
# from pystruct.models import ChainCRF
# from pystruct.learners import FrankWolfeSSVM
# import collections
# import itertools

import learntok
import pickle

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


def main():
  parser = argparse.ArgumentParser(description="segment+tokenize given an established model",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--untokfile", "-u", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="untok file")
  parser.add_argument("--modelfile", "-m", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="pickled model file (model, featuremap, labelmap)")
  parser.add_argument("--bio", "-b", action='store_true', default=False, help="output bio instead of characters")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output (bio) file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  untokfile = prepfile(args.untokfile, 'r')
  outfile = prepfile(args.outfile, 'w')


  modelblock = pickle.load(args.modelfile)
  model = modelblock['model']
  featmap = modelblock['feats']
  labelmap = modelblock['labels']
  
  data = []
  labels = []
  maplabels = []
  for untokline in untokfile:
    isStart = True
    feats, _ = learntok.numberize_features(np.array([learntok.featurize(untokline.strip()),]), None, dv=featmap)
#    print(feats)
#    print(feats.shape)
#    print(feats[0][0].shape)
    preds = labelmap.inverse_transform(model.predict(feats))
#    print(preds)
#     print(preds[0].shape)
    lastLabel=None
    for char, label in zip(list(untokline.strip()), preds[0]):
      if args.bio:
        if not isStart:
          outfile.write(" ")
        outfile.write(label)
        isStart = False
      else:
        # TODO: upgrade this for biosn
        if (label=='B' and lastLabel=='B') or (label=='B' and lastLabel=='I'):
          outfile.write(' ')
        outfile.write(char)
        lastLabel=label
        # check for problems
        if label=='O' and char != ' ':
          sys.stderr.write("warning: class O for %s\n" % char)
        if lastLabel is None and label != 'B':
          sys.stderr.write("warning: non-B (%s) for starting symbol %s\n" % (label, char))
        if lastLabel =='O' and label == 'I':
          sys.stderr.write("warning: OI at %s\n" % char)
    outfile.write('\n')
if __name__ == '__main__':
  main()


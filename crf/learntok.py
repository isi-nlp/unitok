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
from pystruct.learners import FrankWolfeSSVM, SubgradientSSVM
import collections
import itertools
import pickle

if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip

scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


#http://stackoverflow.com/questions/9518806/how-to-split-a-string-on-whitespace-and-retain-offsets-and-lengths-of-words
# called 'using_split2'
# note: returns (0, 3) for "abc" to better integrate below
def wstok_offsets(line, _len=len):
  ''' return whitsepace-tokenized line and character offsets '''
  words = line.split()
  index = line.index
  offsets = []
  append = offsets.append
  running_offset = 0
  for word in words:
    word_offset = index(word, running_offset)
    word_len = _len(word)
    running_offset = word_offset + word_len
    append((word, word_offset, running_offset))
  return offsets

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

def puncid(line, pos):
  ''' if punctuation, the literal character value '''
  cc = charclass(line, pos, True)
  if cc == 'P':
    return line[pos]
  return "X"

def charid(line, pos):
  ''' the literal character value (blows up model) '''
  return line[pos]

def lastcharid(line, pos):
  ''' the last literal character value (blows up model) '''
  return "XS" if pos == 0 else charid(line, pos-1)

def nextcharid(line, pos):
  ''' the next literal character value (blows up model) '''
  return "XE" if pos+1 == len(line) else charid(line, pos+1)

def isrepeat(line, pos):
  ''' is this character the same as the last character? '''
  return "XS" if pos == 0 else str(line[pos] == line[pos-1])

def willrepeat(line, pos):
  ''' is this character the same as the next character? '''
  return "XE" if pos+1 == len(line) else str(line[pos] == line[pos+1])


# regular features in use
features = {
  'currclass': currclass,
  'lastclass': lastclass,
  'nextclass': nextclass,
  'puncid': puncid,
  'charid': charid,
  'lastcharid': lastcharid,
  'nextcharid': nextcharid,
  'isrepeat': isrepeat,
  'willrepeat': willrepeat,
           }


def iscap(tok):
  ''' is this token capitalized '''
  for pos in range(len(tok)):
    cc = charclass(tok, pos, False)
    if cc.startswith("L"):
      return cc == "Lu" or cc == "Lt"
  return False

def toklen(tok):
  ''' how long is this token? '''
  return len(tok)

def ishotfix(tok):
  ''' specifcally identify problem spots for debugging '''
  # NOTE: only matches the first it sees
  for srchstr in ("Mr.", "Maj.", "Gen."):
    if tok.find(srchstr) > 0:
      return srchstr
  return "X"

# pre-tok global features in use
# all features pertain to the original token
# length (done)
# is capitalized (after initial punc) (done)

# looks like email
# looks like hash tag
# looks like url
# punctuation only on ends


tokfeatures = {
  'iscap': iscap,
  'toklen': toklen,
  'ishotfix': ishotfix,
               }


def featurize(line):
  ''' unify char and tok based featurization '''
  charfeats  = char_featurize(line)
  tokfeats = tok_featurize(line)
  ret = []
  for pos in range(len(line)): 
    item = charfeats[pos]
    item.update(tokfeats[pos])
    ret.append(item)
  return np.array(ret)

def char_featurize(line):
  ''' get a feature vector for the line for char-based features'''
  ret = dd(int)
  for pos in range(len(line)):
    vec = {}
    for fname, ffun in features.items():
      vec[fname] = ffun(line, pos)
    ret[pos] = vec
  return ret

def tok_featurize(line):
  ''' get token-based features in a char-based way '''
  ret = dd(lambda: dd(str))
  for (tok, start, end) in wstok_offsets(line):
    for fname, ffun in tokfeatures.items():
      val = ffun(tok)
      for pos in range(start, end):
        ret[pos][fname]=val
  return ret

def numberize_features(dataset, unrolled_dataset, dv=None):
  ''' turn non-numeric features into sparse binary features; also return the feature map '''
  # http://fastml.com/converting-categorical-data-into-numbers-with-pandas-and-scikit-learn/
  # http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.DictVectorizer.html
  if dv is None:
    dv = DictVectorizer(sparse=False) # can we make it true?
    dv = dv.fit(unrolled_dataset.flatten())
  return np.array(list(map(dv.transform, dataset))), dv

def numberize_labels(labelset, unrolled_labelset, le=None):
  ''' turn non-numeric labels into numeric space; also return the feature map '''
  # http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.LabelEncoder.html
  if le is None:
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


def prepdata(untokfile, biofile, debug):
  ''' Create appropriate data for learning along with mappers to make more data '''

  data = []
  mapdata = []
  labels = []
  maplabels = []
  for untokline, bioline in izip(untokfile, biofile):
    feats = featurize(untokline.strip())
    if(debug):
      sys.stderr.write(untokline)
      sys.stderr.write(str(feats))
    data.append(feats)
    mapdata.extend(feats)
    labs = list(bioline.strip())
    labels.append(labs)
    maplabels.extend(labs)
  data, datamap = numberize_features(np.array(data), np.array(mapdata))
  labels, labelmap = numberize_labels(np.array(labels), np.array(maplabels))
  return data, labels, datamap, labelmap
  
def main():
  parser = argparse.ArgumentParser(description="learn to tokenize",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--untokfile", "-u", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="untok file")
  parser.add_argument("--biofile", "-b", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="bio file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('wb'), default=None, help="output file")
  parser.add_argument("--debug", "-d", action='store_true', default=False, help="debug mode")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  untokfile = prepfile(args.untokfile, 'r')
  biofile = prepfile(args.biofile, 'r')


  data, labels, datamap, labelmap = prepdata(untokfile, biofile, args.debug)

#  print(data)
#  print(labels)
  model = ChainCRF()
  #ssvm = SubgradientSSVM(model=model, C=.1)#, show_loss_every=5)
  ssvm = FrankWolfeSSVM(model=model, max_iter=100, C=.1)#, show_loss_every=5)
  ssvm.fit(data, labels)
  #  curve = ssvm.loss_curve_
  # TONT
  # print("TONT score with chain CRF: %f" % ssvm.score(data, labels))

  ret = {}
  ret['model']=ssvm
  ret['feats']=datamap
  ret['labels']=labelmap
  if args.outfile is not None:
    pickle.dump(ret, args.outfile)

  # print(data[0])
  # print(data.shape)
  # print(np.array([data[0],]).shape)
  # preds = ssvm.predict(np.array([data[0],]))
  # print(preds)
if __name__ == '__main__':
  main()


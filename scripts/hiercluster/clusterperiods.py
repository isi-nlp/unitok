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
from sklearn.cluster import KMeans
import collections
import itertools
import pickle

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


def charclass(line, pos, short):
  ''' what is the character class of the character at pos. and is it shorthand or not? '''
  char = line[pos]
  cclass = ud.category(char)
  return cclass[0] if short else cclass

def classoffset(line, pos, offset):
  ''' generalization of which character value '''
  if pos+offset <= 0:
    return "XS"
  if pos+offset >= len(line):
    return "XE"
  return charclass(line, pos+offset, True)

def currclass(line, pos):
  return classoffset(line, pos, 0)

def lastclass(line, pos):
  return classoffset(line, pos, -1)

def nextclass(line, pos):
  return classoffset(line, pos, +1)

def charid(line, pos):
  ''' the literal character value (blows up model) '''
  return line[pos]

def charidoffset(line, pos, offset):
  ''' generalization of which character value '''
  if pos+offset <= 0:
    return "XS"
  if pos+offset >= len(line):
    return "XE"
  return charid(line, pos+offset)

def lastcharid(line, pos):
  ''' the last literal character value (blows up model) '''
  return charidoffset(line, pos, -1)

def nextcharid(line, pos):
  ''' the next literal character value (blows up model) '''
  return charidoffset(line, pos, +1)

def isrepeat(line, pos):
  ''' is this character the same as the last character? '''
  return "XS" if pos == 0 else str(line[pos] == line[pos-1])

def willrepeat(line, pos):
  ''' is this character the same as the next character? '''
  return "XE" if pos+1 == len(line) else str(line[pos] == line[pos+1])

# regular features in use
features = {
  'currclass': currclass,
  'charid': charid,
#  'isrepeat': isrepeat,
#  'willrepeat': willrepeat,
           }

# TODO: punkt-inspired features
# length of token minus periods
# number of internal periods in current (or next) token
# is internal period (no whitespace on either side)

# TODO: web features
# contains p:// (urlish)
# contains @ (emailish)

def featurize(line, pos):
  ''' get a feature vector for the line at that pos'''
  vec = {}
  for fname, ffun in features.items():
    vec[fname] = ffun(line, pos)
  return vec

def numberize_features(dataset, dv=None):
  ''' turn non-numeric features into sparse binary features; also return the feature map '''
  # http://fastml.com/converting-categorical-data-into-numbers-with-pandas-and-scikit-learn/
  # http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.DictVectorizer.html
  if dv is None:
    dv = DictVectorizer(sparse=False) # can we make it true?
    dv = dv.fit(dataset)
  return dv.transform(dataset), dv


def prepdata(textfile, targets, debug, uselookahead=True):
  ''' Create appropriate data for learning along with mappers to make more data '''
  from itertools import tee
  data = []
  info = []
  textfile, textfilefuture = tee(textfile)
  textfilefuture.__next__()
  for line, nextline in izip(textfile, textfilefuture):
    if(debug):
      sys.stderr.write(line)
    linewithlookahead = line.strip()+" "+nextline if (uselookahead and nextline is not None) else line
    for target in targets:
      srchstart = 0
      lastloc = line.find(target)
      while lastloc >=0:
        feats = featurize(linewithlookahead, lastloc)
        info.append((linewithlookahead[max(0, lastloc-10):min(len(linewithlookahead), lastloc+10)].strip(), target, lastloc))
        if (debug):
          sys.stderr.write("Pos %d: %s\n" % (lastloc, str(feats)))
        data.append(feats)
        srchstart = lastloc+1
        lastloc = line.find(target, srchstart)
#  print(len(data))
  data, datamap = numberize_features(data)
#  print(data[0])
#  print(data[0].shape)
  return data, info, datamap


def main():
  parser = argparse.ArgumentParser(description="k means clustering for periods. see unitok/scripts/learntok for some inspiration",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('wb'), default=None, help="output file")
  parser.add_argument("--tontfile", "-t", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="test on train output file")
  parser.add_argument("--kclusters", "-k", default=2, type=int, help="number of clusters")
  parser.add_argument("--leftcontext", "-l", default=5, type=int, help="make features for this number of previous characters")
  parser.add_argument("--rightcontext", "-r", default=0, type=int, help="make features for this number of next characters")
  parser.add_argument("--possibles", "-p", nargs='+', default=['.'], help="set of characters to possibly split on")
  parser.add_argument("--debug", "-d", action='store_true', default=False, help="debug mode")


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


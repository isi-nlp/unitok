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
import numpy as np # pip install numpy
import scipy as sp
import sklearn
from sklearn.feature_extraction import DictVectorizer # pip install sklearn
from sklearn.cluster import MiniBatchKMeans, KMeans, DBSCAN
import collections
import itertools
import pickle
import random
import copy
import ast
from collections import Counter
if int(sklearn.__version__.split('.')[0]) > 0 or int(sklearn.__version__.split('.')[1]) > 17:
  from sklearn.exceptions import NotFittedError
else:
  from sklearn.utils.validation import NotFittedError
from colorama import Fore, Back, Style # pip install colorama

scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')

# http://stackoverflow.com/questions/27822752/scikit-learn-predicting-new-points-with-dbscan
class pDBSCAN(DBSCAN):
  def predict(self, X_new, metric=sp.spatial.distance.cosine):
    # Result is noise by default
    y_new = np.ones(shape=X_new.shape[0], dtype=int)*-1 

    # Iterate all input samples for a label
    for j, x_new in enumerate(X_new):
      # Find a core sample closer than EPS
      for i, x_core in enumerate(self.components_): 
        if metric(x_new, x_core) < self.eps:
          # Assign label of x_core to x_new
          y_new[j] = self.labels_[self.core_sample_indices_[i]]
          break

    return y_new

# url matcher. https://gist.github.com/dperini/729294
# python port by adam rofer
URL_REGEX = re.compile(
    u"^"
    # protocol identifier
    u"(?:(?:https?|ftp)://)"
    # user:pass authentication
    u"(?:\S+(?::\S*)?@)?"
    u"(?:"
    # IP address exclusion
    # private & local networks
    u"(?!(?:10|127)(?:\.\d{1,3}){3})"
    u"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
    u"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
    # IP address dotted notation octets
    # excludes loopback network 0.0.0.0
    # excludes reserved space >= 224.0.0.0
    # excludes network & broadcast addresses
    # (first & last IP address of each class)
    u"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
    u"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
    u"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
    u"|"
    # host name
    u"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
    # domain name
    u"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
    # TLD identifier
    u"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
    u")"
    # port number
    u"(?::\d{2,5})?"
    # resource path
    u"(?:/\S*)?"
    u"$"
    , re.UNICODE)

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


def charclass(line, pos, short):
  ''' what is the character class of the character at pos. and is it shorthand or not? '''
  char = line[pos]
  cclass = ud.category(char)
#  print("%d of %s is %s; class is %s" % (pos, line, char, cclass))
  return cclass[0] if short else cclass

def classoffset(line, pos, offset, short=True):
  ''' generalization of which character value '''
#  print("Getting class of %d offset by %d in %s" % (pos, offset, line))
  if pos+offset < 0:
    return "XS"
  if pos+offset >= len(line):
    return "XE"
  return charclass(line, pos+offset, short)

def currclass(line, pos, short=True):
  return classoffset(line, pos, 0, short=short)


def charid(line, pos):
  ''' the literal character value (blows up model) '''
  return line[pos]

def charidoffset(line, pos, offset):
  ''' generalization of which character value '''
  if pos+offset < 0:
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

def ispattern(line, pos, offset):
  ''' generalization of isrepeat: look for a 'same character' offset away from pos '''
  if pos+offset < 0:
    return "XS"
  if pos+offset >= len(line):
    return "XE"
  return str(line[pos] == line[pos+offset])

def isrepeat(line, pos):
  ''' is this character the same as the last character modulo jump of x? '''
  return ispattern(line, pos, -1)

def willrepeat(line, pos):
  ''' is this character the same as the next character? '''
  return ispattern(line, pos, +1)

def ismultipattern(line, pos, offset, times):
  ''' is this the same as last modulo jump of offset, 2offset, ...times*offset? '''
  try:
    for i in range(1, times+1):
      if not ast.literal_eval(ispattern(line, pos, offset*i)):
        return 'False'
  except ValueError:
    return 'False'
  return str('True')
  

# TODO: punkt-inspired features
# length of token minus periods
# number of internal periods in current (or next) token
# is internal period (no whitespace on either side)

# TODO: web features
# contains p:// (urlish)
# contains @ (emailish)


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

def isurl(tok):
  ''' does this token look like  a url? '''
  return URL_REGEX.match(tok) is not None


def featurize(line, pos, features):
  ''' get a feature vector for the line at that pos'''
  vec = {}
  for fname, ffun in features.items():
    vec[fname] = ffun(line, pos)
  return vec

def tok_featurize(line, tokfeatures, externals): # externals are used by ffun
  ''' get token-based features in a char-based way '''
  ret = dd(lambda: dd(str))
  for (tok, start, end) in wstok_offsets(line):
    for fname, ffun in tokfeatures.items():
      val = ffun(tok)
      for pos in range(start, end):
        ret[pos][fname]=val
  return ret


def numberize_features(dataset, sparse=True, dv=None):
  ''' turn non-numeric features into sparse binary features; also return the feature map '''
  # http://fastml.com/converting-categorical-data-into-numbers-with-pandas-and-scikit-learn/
  # http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.DictVectorizer.html
  if dv is None:
    dv = DictVectorizer(sparse=sparse)
    dv = dv.fit(dataset)
  return dv.transform(dataset), dv


def prepdata(textfile, features, tokfeatures, debug, settings, uselookahead=True, dv=None):
  ''' Create appropriate data for learning along with mappers to make more data '''
  from itertools import tee
  data = []
  info = []
  window=10
  targets = settings['possibles'] if 'possibles' in settings else []
  removetargets = settings['removepossibles'] if 'removepossibles' in settings else []
  externals = settings['externalfeatures'] if 'externalfeatures' in settings else []
  sparse = settings['sparse'] if 'sparse' in settings else True
  isTargetPunc = settings['unicodepossibles'] if 'unicodepossibles' in settings else False
  textfile, textfilefuture = tee(textfile)
  textfilefuture.__next__()
#  for ln, (line, nextline) in enumerate(izip(textfile, textfilefuture)):
  for ln, line in enumerate(textfile):
    try:
      nextline = textfilefuture.__next__()
    except StopIteration:
      nextline = None
    if(debug):
      sys.stderr.write(line)
    tokfeats = tok_featurize(line, tokfeatures, externals)
    linewithlookahead = line.strip('\n')+" "+nextline if (uselookahead and nextline is not None) else line
    iterline = list(line.strip())
    moditerline = list(map(lambda x: ud.category(x)[0], iterline)) if isTargetPunc else iterline
    for lastloc, (tok, origtok) in enumerate(zip(moditerline, iterline)):
      if tok in targets and origtok not in removetargets:
        feats = featurize(linewithlookahead, lastloc, features)
        feats.update(tokfeats[lastloc])
        prefix = linewithlookahead[max(0, lastloc-window):lastloc]
#        print("Line: "+linewithlookahead)
#        print("Prefix: ["+prefix+"]")
        prefix = Fore.BLUE+'_'*(window-len(prefix))+Fore.RESET+prefix
        suffix = linewithlookahead[lastloc+1:min(len(linewithlookahead), lastloc+window+1)].rstrip('\n')
#        print("Suffix: ["+suffix+"]")
#        sys.exit(1)
        suffix = suffix+Fore.BLUE+'_'*(window-len(suffix))+Fore.RESET
        infoblock = {'prefix':prefix,
                     'char':linewithlookahead[lastloc],
                     'suffix':suffix,
                     'ln':ln,
                     'offset':lastloc,
                     'feats':feats}
        info.append(infoblock)
        if (debug):
          sys.stderr.write("Pos %d: %s\n" % (lastloc, str(feats)))
        data.append(feats)

#  print(len(data))
  data, datamap = numberize_features(data, sparse=sparse, dv=dv)
#  print(data[0])
#  print(data[0].shape)
  return data, np.array(info), datamap

def formatContext(line, docolor=True):
  ''' put color formatting around parts of an info tuple '''
  prefix=line['prefix'][:-1]
  lastpre=Fore.GREEN+Style.BRIGHT+line['prefix'][-1]+Style.RESET_ALL if docolor else line['prefix'][-1]
  target=Fore.RED+Style.BRIGHT+line['char']+Style.RESET_ALL if docolor else line['char']
  firstsuff=Fore.GREEN+Style.BRIGHT+line['suffix'][0]+Style.RESET_ALL if docolor else line['suffix'][0]
  suffix=line['suffix'][1:]
  displaystr=prefix+lastpre+target+firstsuff+suffix
  return displaystr


class ModelTree:
  def getNode(modelTree, address):
    ''' traverse down the tree to find the node matching the given address '''
    if address=="<root>":
      return modelTree
    addressnums = map(int, address.split('.'))
    ret = modelTree
    sofar = []
    for num in addressnums:
      if num not in ret.children:
        sys.stderr.write("Couldn't get %s; returning %s\n" % (address, '.'.join(map(str, sofar))))
        break
      ret = ret.children[num]
      sofar.append(num)
    return ret
  
  def __init__(self, modeltype, data, info, label=0, modelparams=[], modelkwargs={}, parent=None):
    self.modeltype = modeltype
    self.modelparams = modelparams
    self.modelkwargs = modelkwargs
    self.model = None if modeltype is None else modeltype(*modelparams, **modelkwargs)
    self.data = data
    self.info = info
    self.label = label
    self.handlabel = None
    self.parent = parent
    self.children = {}
    #self.handlabels = {}
    #self.leafdata = {} # filled by classifydata when model leaves are hit
    #self.leafinfo = {} # filled by classifydata when model leaves are hit

  def add(self, modelTree, label):
    self.children[label] = modelTree

  def getFullLabel(self, labels=[]):
    ''' retrieve full hierarchy label '''
    if self.parent is None:
      if len(labels) == 0:
        return "<root>"
      return '.'.join(map(str, labels))
    else:
      labels.insert(0, self.label)
      return self.parent.getFullLabel(labels)

  def clean(self):
    self.info = None
    for _, child in self.children.items():
      child.clean()


  def handlabeldata(self, data):
    ''' recursively traverse through tree and assign handlabel to data '''
    if self.handlabel is not None and self.handlabel != 'r':
      return np.array([self.handlabel,]*data.shape[0])
    if self.model is None:
      fulllabel = self.getFullLabel([])
      return np.array([fulllabel,]*data.shape[0])
    result = self.model.predict(data)
    ret = np.empty(result.shape, dtype=np.dtype(('U', 100)))
    for value in set(result):
      subresult = self.children[value].handlabeldata(data[result==value])
      ret[result==value] = np.array(subresult, dtype=np.dtype(('U', 100)))
    return ret

  def labeldata(self, data):
    ''' recursively traverse through tree and assign label to data '''
    if self.model is None:
      return None
    result = self.model.predict(data)
    strresult = np.array(list(map(str, result)))
    if len(self.children) == 0:
      return strresult
    else:
      ret = np.empty(result.shape, dtype=np.dtype(('U', 100)))
      for value in set(result):
        if value not in self.children:
          ret[result==value] = strresult[result==value]
        else:
          subresult = self.children[value].labeldata(data[result==value])
          if subresult is None:
            ret[result==value] = strresult[result==value]
          else:
            combination = list(map(lambda x: "%s.%s" % (x[0], x[1]), zip(strresult[result==value], subresult)))
            ret[result==value] = np.array(combination, dtype=np.dtype(('U', 100)))
    return ret

  def printSamples(self, samples=20):
    sampleset = range(len(self.info)) if len(self.info) <= samples else np.random.choice(len(self.info), replace=False, size=(samples,))
    for ln in sampleset:
      line = self.info[ln]
      print(formatContext(line))

  def handLabel(self, samples=20, values=[('B', "Begin"), ('I', "In"), ('O', "Out")], annfile=None, refine=False):
    ''' interactively assign labels to clusters based on visual inspection of samples '''
    fullLabel = self.getFullLabel([])
    print("Samples for cluster %s" % fullLabel)
    if self.handlabel is not None:
      print("Previous label: "+self.handlabel)
    print(self.info.shape)
    self.printSamples(samples=samples)
    result = None
    localvalues = copy.copy(values)
    localvalues.append(("m", "more")) # more
    localvalues.append(("q", "quit")) # quit
    if self.model is not None or refine:
      localvalues.append(("r", "refine"))
    while result is None:
      resp = input(" label ( %s ) ? >>" % ' '.join(map(lambda x: "%s=%s" % x, localvalues)))
      if resp not in map(lambda x: x[0], localvalues):
        print("Please choose from the available labels")
      else:
        result = resp
      if result == "m":
        self.printSamples(samples=samples)
        result = None
    if result == "q":
      return True
    self.handlabel = result
    if annfile is not None:
      annfile.write("%s\t%s\n" % (result, fullLabel))
      annfile.flush()
    if result == "r":
      if len(self.children) == 0:
        self.refine()
      for _, child in self.children.items():
        if child.handLabel(samples=samples, values=values, annfile=annfile, refine=refine):
          return True


  # TODO: fix this for None refinement 
  def refine(self):
    ''' create submodels for this model '''
    if len(self.children) > 0:
      sys.stderr.write("Not overwriting existing refinement\n")
      return
    sys.stderr.write("Dynamically refining\n")
    try:
      labels = self.model.predict(self.data)
    except NotFittedError:
      labels = self.model.fit_predict(self.data)
    for label in set(labels):
      subset = self.data[labels==label]
      subinfo = self.info[labels==label]
      nextmodel = ModelTree(self.modeltype, subset, subinfo, label=label, modelparams=self.modelparams, modelkwargs=self.modelkwargs, parent=self)
      self.add(nextmodel, label)


  def classifydata(self, data, info, goldlabels, ofh, thresh=0.75):
    ''' predict on new data and propagate that data down. useful for auto-labeling '''
    self.data = data
    self.info = info
    mostcommon = Counter(goldlabels).most_common(1)
    if mostcommon[0][1]/len(goldlabels) >= thresh or self.model is None:
      self.handlabel = mostcommon[0][0]
      ofh.write("%s\t%s\t%f\n" % (self.getFullLabel([]), mostcommon[0][0], mostcommon[0][1]/len(goldlabels)))
      return
    else:
#      for k, v in Counter(goldlabels).items():
#        print("%s\t%s\t%f" % (self.getFullLabel([]), k, v/len(goldlabels)))
#      print("-----")
      labels = self.model.predict(self.data)
      for label in set(labels):
        subgold = goldlabels[labels==label]
        if label in self.children:
          subset = self.data[labels==label]
          subinfo = self.info[labels==label]
          self.children[label].classifydata(subset, subinfo, subgold, ofh, thresh=thresh)
        else:
          sys.stderr.write("Error: %s not found in children of %s\n" % (label, self.getFullLabel([])))
          sys.exit(1)
          # self.leafdata[label] = subset
          # self.leafinfo[label] = subinfo
          # submostcommon = Counter(subgold).most_common(1)
          # self.handlabels[label] = submostcommon[0][0]
          # ofh.write("%s.%d\t%s\t%f\n" % (self.getFullLabel([]), label, submostcommon[0][0], submostcommon[0][1]/len(subgold)))
      return
    
def prepfeatures(settings):
  # regular features in use
  features = {
    'currclass': currclass,
    'charid': charid,
    'isrepeat': isrepeat,
    'willrepeat': willrepeat,
  }
  if 'extendedpatterns' in settings and settings['extendedpatterns']:
    extfeats = {
      'isrep2' : lambda x, y: ispattern(x, y, -2),
      'isrep3' : lambda x, y: ispattern(x, y, 2),
      'willrep2' : lambda x, y: ispattern(x, y, -3),
      'willrep3' : lambda x, y: ispattern(x, y, 3),
      'isrep2x2' : lambda x, y: ismultipattern(x, y, -2, 2),
      'isrep3x2' : lambda x, y: ismultipattern(x, y, -3, 2),
      'willrep2x2' : lambda x, y: ismultipattern(x, y, 2, 2),
      'willrep3x2' : lambda x, y: ismultipattern(x, y, 3, 2)
    }
    features.update(extfeats)
  short = settings['short'] if 'short' in settings else True
  if settings['leftcontext'] > 0:
    for i in range(1, settings['leftcontext']+1):
      features['class-%d' % i] = lambda x, y, i=i: classoffset(x, y, -i, short=short)
      if settings['charfeature']:
        features['char-%d' % i] = lambda x, y, i=i: charidoffset(x, y, -i)
  if settings['rightcontext'] > 0:
    for i in range(1, settings['rightcontext']+1):
      features['class+%d' % i] = lambda x, y, i=i: classoffset(x, y, i, short=short)
      if settings['charfeature']:
        features['char+%d' % i] = lambda x, y, i=i: charidoffset(x, y, i)

  tokfeatures = {
    'iscap': iscap,
    'toklen': toklen,
    'isurl': isurl,
  }
  # external features become tok features
  externalfeats = {}
  if 'externalfeatures' in settings and settings['externalfeatures'] is not None:
    for fname, data in settings['externalfeatures'].items():
      # kludgy way to get dimensionality: look at the first record
      datalen = 0
      for tupword, tup in data.items():
        datalen = len(tup)
        break
      for i in range(datalen):
        def fun(x, externals=settings['externalfeatures'], fname=fname, i=i):
          if x not in externals[fname]: # externals should be passed to prepfeatures
            return 0
          return externals[fname][x][i]
        externalfeats["%s.%d" % (fname, i)] = fun
    tokfeatures.update(externalfeats)
  bannedfeats = settings['banned'] if 'banned' in settings else []

  for feat in copy.copy(tokfeatures).keys():
    if feat in bannedfeats:
      tokfeatures.pop(feat)
  #print(tokfeatures)
  return features, tokfeatures

def prepexternals(fh):
  ''' given file of the form word \t feature1 \t feature2... make a simple dict to the array of feats '''
  # TODO: if needed, make the dict a dd templated on an empty vector of the proper length
  ret = {}
  for line in fh:
    toks = line.strip().split('\t')
    ret[toks[0]] = list(map(float, toks[1:]))
  return ret

def main():
  parser = argparse.ArgumentParser(description="k means clustering for periods. see unitok/scripts/learntok for some inspiration",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('wb'), default=None, help="output file")
  parser.add_argument("--externalfiles", "-e", nargs='+', default=[], type=argparse.FileType('r'), help="extra feature files")
  parser.add_argument("--tontfile", "-t", nargs='?', type=argparse.FileType('w'), default=None, help="test on train output file")
  parser.add_argument("--unicodepossibles", "-u", action='store_true', default=False, help="interpret possibles list as unicode class prefixes")
  parser.add_argument("--kclusters", "-k", default=2, type=int, help="number of clusters per layer")
#  parser.add_argument("--clean", "-c", action='store_true', default=False, help="clean model training (no tont)")
  parser.add_argument("--layers", "-y", default=1, type=int, help="number of layers")
  parser.add_argument("--minclustersize", "-z", default=10.0, type=float, help="no cluster splitting below this pct of training data")
  parser.add_argument("--leftcontext", "-l", default=5, type=int, help="make features for this number of previous characters")
  parser.add_argument("--rightcontext", "-r", default=0, type=int, help="make features for this number of next characters")
  parser.add_argument("--nochar", "-n", action='store_false', dest='charfeature', default=True,  help="no character features (class only)")
  parser.add_argument("--longclass", action='store_false', dest='shortclass', default=True,  help="use full character class instead of initial symbol")
  parser.add_argument("--possibles", "-p", nargs='+', default=['.'], help="set of characters to possibly split on")
  parser.add_argument("--removepossibles", "-v", nargs='+', default=[], help="set of characters from the possibles list to not split on (helpful for removing period, comma, etc")
  parser.add_argument("--handlabel", "-H", action='store_true', default=False, help="do hand labeling after training")
  parser.add_argument("--dbscan", action='store_true', default=False, help="try dbscan instead of kmeans")
  parser.add_argument("--debug", "-d", action='store_true', default=False, help="debug mode")
  parser.add_argument("--banned", nargs='+', default=[], help='tok-based features to remove')
  parser.add_argument("--paramnames", nargs='+', default=[], help='algorithm parameter names')
  parser.add_argument("--paramvals", nargs='+', default=[], help='algorithm parameter values')
  parser.add_argument("--noformat", action='store_false', dest='format', default=True, help="turn off color formatting in tont")
  parser.add_argument("--expat", action='store_true', default=False, help="add some extended repeating patterns")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  tontfile = prepfile(args.tontfile, 'w') if args.tontfile is not None else None
  externalfiles = {}
  for fh in args.externalfiles:
    externalfiles[fh.name] = prepexternals(prepfile(fh, 'r'))
    
  settings = {}
  settings['kclusters'] = args.kclusters
  settings['layers'] = args.layers
  settings['minclustersize'] = args.minclustersize
  settings['leftcontext'] = args.leftcontext
  settings['rightcontext'] = args.rightcontext
  settings['possibles'] = args.possibles
  settings['removepossibles'] = args.removepossibles
  settings['unicodepossibles'] = args.unicodepossibles
  settings['charfeature'] = args.charfeature
  settings['banned'] = args.banned
  settings['short'] = args.shortclass
  settings['extendedpatterns'] = args.expat
  settings['externalfeatures'] = externalfiles

  features, tokfeatures = prepfeatures(settings)
  

  modeltype = MiniBatchKMeans
  modelkwargs = {'n_clusters':args.kclusters}
  sparse = True
  if args.dbscan:
    modeltype = pDBSCAN
    modelkwargs = {'eps':0.2}
    sparse = False

  settings['sparse']=sparse
  if len(args.paramnames) != 0:
    modelkwargs = dict(zip(args.paramnames, map(float, args.paramvals)))

  #print(modelkwargs)


#  print("Preparing data")
  data, info, datamap = prepdata(infile, features, tokfeatures, args.debug, settings)

#  print("Done")
  #print(data.shape)
  if(args.debug):
    print(data)


  modelTree = ModelTree(modeltype, data, info, modelkwargs=modelkwargs)

  datathresh = data.shape[0]*args.minclustersize/100

  # top-down k-means clustering:
  # for each layer
  #   for each data setx
  #     if the set is large enough
  #       cluster the set
  #       put the clustered data in the next queue
  #       add the cluster models to the model set

  printoutqueue = []
  modelqueue = [modelTree,]
  for layer in range(args.layers):
    print("Layer %d" % layer)
    nextmodelqueue = []
    if len(modelqueue) == 0:
      break
    for lastmodel in modelqueue:
      if lastmodel.parent is not None:
        printoutqueue.append(lastmodel)
      #print("Layer %d: classifying %d items for model %s" % (layer, lastmodel.data.shape[0], lastmodel.getFullLabel([])))
      labels = lastmodel.model.fit_predict(lastmodel.data)
      for label in set(labels):
        subset = lastmodel.data[labels==label]
        subinfo = lastmodel.info[labels==label]
        if layer < args.layers-1 and subset.shape[0] > datathresh:
          nextmodel = ModelTree(modeltype, subset, subinfo, label=label, modelkwargs=modelkwargs, parent=lastmodel)
          nextmodelqueue.append(nextmodel)
          lastmodel.add(nextmodel, label)
        else:
          nextmodel = ModelTree(None, subset, subinfo, label=label, modelkwargs=modelkwargs, parent=lastmodel)
          lastmodel.add(nextmodel, label)
          printoutqueue.append(nextmodel)
    modelqueue = nextmodelqueue

  if args.handlabel:
    # TODO: pass options!
    modelTree.handLabel()

  if tontfile is not None:
    for model in printoutqueue:
      modelLabel = model.getFullLabel([])
      if model.handlabel is not None:
        modelLabel = modelLabel+"("+model.handlabel+")"
      tontfile.write("%s\t%d\n" % (modelLabel, len(model.info)))
      for elem in model.info:
        tontfile.write("%s\t%s\t%s\n" % (modelLabel, formatContext(elem, args.format), str(elem['feats'])))


  
  if args.outfile is not None:
    #modelTree.clean()
    ret = {}
    ret['model'] = modelTree
    ret['feats'] = datamap
    ret['settings'] = settings
    pickle.dump(ret, args.outfile)

if __name__ == '__main__':
  main()


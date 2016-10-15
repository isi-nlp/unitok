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
import tempfile
import shutil
import atexit
scriptdir = os.path.dirname(os.path.abspath(__file__))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')

# for populating vocabulary
# modified from
# http://stackoverflow.com/questions/279561/what-is-the-python-equivalent-of-static-variables-inside-a-function
class Inc():
  def __init__(self):
    self.c = -1
  def inc(self):
    self.c+=1
    return self.c

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
  parser = argparse.ArgumentParser(description="training and bio data to ff nn training format",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input text file")
  parser.add_argument("--biofile", "-b", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input bio file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output integerized training file")
  parser.add_argument("--invocabfile", "-v", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output 1wpl input vocab file")
  parser.add_argument("--outvocabfile", "-V", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output 1wpl output vocab file")
  parser.add_argument("--context", "-c", default=5, type=int, help="context window")

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  biofile = prepfile(args.biofile, 'r')
  outfile = prepfile(args.outfile, 'w')
  invocabfile = prepfile(args.invocabfile, 'w')
  outvocabfile = prepfile(args.outvocabfile, 'w')

  invinc = Inc()
  invocab = dd(lambda: invinc.inc())
  def iv(x):
#    return x
    return invocab[x] 
  outvinc = Inc()
  outvocab = dd(lambda: outvinc.inc())
  def ov(x):
#    return x
    return outvocab[x] 

  for textline, bioline in izip(infile, biofile):
    textline = textline.strip()
    bioline = bioline.strip()
    lastcontext = []
    for i in range(args.context):
      lastcontext.append(iv("BOS"))
    for pos in range(len(textline)):
      # get next context
      nextcontext = []
      ras = min(pos+1, len(textline))
      rae = min(len(textline), ras+args.context)
      for np in range(ras, rae):
        try:
          nextcontext.append(iv(textline[np]))
        except IndexError:
          print(np, len(textline), ras, rae)
          sys.exit(1)
      while len(nextcontext) < args.context:
        nextcontext.append(iv("EOS"))
      # make line
      outfile.write(' '.join(map(str, lastcontext+[iv(textline[pos]),]+nextcontext+[ov(bioline[pos]),]))+"\n")
      # update pre context
      for i in range(args.context-1):
        lastcontext[i]=lastcontext[i+1]
      lastcontext[args.context-1]=iv(textline[pos])
  # dump vocabs
  for invoc in sorted(invocab.items(), key=lambda x: x[1]):
    char = "SPACE" if invoc[0] == " " else invoc[0]
    invocabfile.write(char+"\n")
  for outvoc in sorted(outvocab.items(), key=lambda x: x[1]):
    outvocabfile.write(outvoc[0]+"\n")
if __name__ == '__main__':
  main()

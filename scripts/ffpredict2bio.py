#!/usr/bin/env python
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
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
  parser = argparse.ArgumentParser(description="given integerized one output per line, original input, and dictionary, produce bio file for further processing",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--nnfile", "-n", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="nn file (integerized one output per line)")
  parser.add_argument("--origfile", "-g", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="original file (same chars as nn file has lines but multi per line")
  parser.add_argument("--vocabfile", "-v", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="vocab file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output biofile")

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  atexit.register(cleanwork)


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  nnfile = prepfile(args.nnfile, 'r')
  origfile = prepfile(args.origfile, 'r')
  vocabfile = prepfile(args.vocabfile, 'r')
  outfile = prepfile(args.outfile, 'w')

  vocab = []
  for line in vocabfile:
    vocab.append(line.strip())
  nnres = []
  for line in nnfile:
    nnres.append(vocab[int(line.strip())])
  for line in origfile:
    linelen = len(line.strip())
    outfile.write(''.join(nnres[:linelen])+"\n")
    nnres = nnres[linelen:]


if __name__ == '__main__':
  main()

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
from itertools import chain, combinations
scriptdir = os.path.dirname(os.path.abspath(__file__))

# https://docs.python.org/2/library/itertools.html
def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

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

def udize(word, excludeP=True, excludeS=True):
  codes = []
  for sym in list(word):
    code = ud.category(sym)
    if excludeP and code.startswith("P"):
      codes.append(sym)
    elif excludeS and code.startswith("S"):
      codes.append(sym)
    else:
      codes.append(code)
  return ''.join(codes)

def main():
  parser = argparse.ArgumentParser(description="given vocabulary, spit out 1gram ud code fsa, ud2word fst, and w2c fst",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output ud fsa file")
  parser.add_argument("--u2wfile", "-u", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output udcode2word file")
  parser.add_argument("--w2cfile", "-w", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output word2char file")


  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')
  u2wfile = prepfile(args.u2wfile, 'w')
  w2cfile = prepfile(args.w2cfile, 'w')



  u2wfile.write("0\n(0")
  w2cfile.write("END\n")
  udwords = set()
  for ln, line in enumerate(infile):
    origword = line.strip()
    word = udize(origword)
    modorigword = origword.replace('"', '\\"')
    modword = word.replace('"', '\\"')
    u2wfile.write(" (0 \"%s\" \"%s\" 1!)" % (modword, modorigword))
    udwords.add(modword)
    chars = ['"quote"' if x == '"' else '"%s"' % x for x in list(origword)]
#    print(word)
#    print(chars)
    w2cfile.write("(START (%d-0 \"%s\" %s 1!))\n" % (ln, modorigword, chars[0]))
    lastcn = 0
    for cn, char in enumerate(chars[1:], start=1):
      w2cfile.write("(%d-%d (%d-%d *e* %s 1!))\n" % (ln, lastcn, ln, cn, char))
      lastcn = cn
    w2cfile.write("(%d-%d (WEND *e* *e* 1!))\n" % (ln, lastcn))
  w2cfile.write("""(WEND (END *e* *e* 1!))
(WEND (START *e* \"space\"))
""")
  u2wfile.write(")\n")
  outfile.write("0\n(0")
  for word in udwords:
    outfile.write(" (0 \"%s\")" % word)
  outfile.write(")\n")

if __name__ == '__main__':
  main()


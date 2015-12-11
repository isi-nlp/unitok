#! /usr/bin/env python
import argparse
import sys
import codecs
from itertools import izip
from collections import defaultdict as dd
import re
import os.path
import gzip
scriptdir = os.path.dirname(os.path.abspath(__file__))
import unicodedata as ud
import pickle

# http://unicode.org/reports/tr29/#Sentence_Boundaries

def hexstr2uni(hexstr):
  return unichr(int(hexstr, 16))

# # grep "STerm=\"Y\"" ucd.nounihan.flat.xml  | sed 's/^ *//' | cut -d' ' -f2 | cut -d'=' -f2 | gsed ':a;N;$!ba;s/\n/, /g' > stermlist
# stermlist = ["0021", "002E", "003F", "0589", "061F", "06D4", "0700", "0701", "0702", "07F9", "0964", "0965", "104A", "104B", "1362", "1367", "1368", "166E", "1735", "1736", "1803", "1809", "1944", "1945", "1AA8", "1AA9", "1AAA", "1AAB", "1B5A", "1B5B", "1B5E", "1B5F", "1C3B", "1C3C", "1C7E", "1C7F", "203C", "203D", "2047", "2048", "2049", "2E2E", "2E3C", "3002", "A4FF", "A60E", "A60F", "A6F3", "A6F7", "A876", "A877", "A8CE", "A8CF", "A92F", "A9C8", "A9C9", "AA5D", "AA5E", "AA5F", "AAF0", "AAF1", "ABEB", "FE52", "FE56", "FE57", "FF01", "FF0E", "FF1F", "FF61", "10A56", "10A57", "11047", "11048", "110BE", "110BF", "110C0", "110C1", "11141", "11142", "11143", "111C5", "111C6", "111CD", "111DE", "111DF", "11238", "11239", "1123B", "1123C", "112A9", "115C2", "115C3", "115C9", "115CA", "115CB", "115CC", "115CD", "115CE", "115CF", "115D0", "115D1", "115D2", "115D3", "115D4", "115D5", "115D6", "115D7", "11641", "11642", "1173C", "1173D", "1173E", "16A6E", "16A6F", "16AF5", "16B37", "16B38", "16B44", "1BC9F", "1DA88"]

# # aterm from report
# stermlist.extend(["2024",]) 
# stermlist = map(hexstr2uni, stermlist)

# # line break = quotation
# # grep "lb=\"QU\"" ucd.nounihan.flat.xml |  sed 's/^ *//' | cut -d' ' -f2 | cut -d'=' -f2 | gsed ':a;N;$!ba;s/\n/, /g' > lbqulist
# lbqulist = ["0022", "0027", "00AB", "00BB", "2018", "2019", "201B", "201C", "201D", "201F", "2039", "203A", "275B", "275C", "275D", "275E", "275F", "2760", "2E00", "2E01", "2E02", "2E03", "2E04", "2E05", "2E06", "2E07", "2E08", "2E09", "2E0A", "2E0B", "2E0C", "2E0D", "2E1C", "2E1D", "2E20", "2E21", "1F676", "1F677", "1F678"]
# lbqulist = map(hexstr2uni, lbqulist)

# #whitespace = y
# #grep "WSpace=\"Y\"" ucd.nounihan.flat.xml | sed 's/^ *//' | cut -d' ' -f2 | cut -d'=' -f2 | gsed ':a;N;$!ba;s/\n/, /g' > wslist
# wslist = ["0009", "000A", "000B", "000C", "000D", "0020", "0085", "00A0", "1680", "2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009", "200A", "2028", "2029", "202F", "205F", "3000"]
# wslist = map(hexstr2uni, wslist)

# geresh = unichr(int('05f3', 16))

# def isclose(unichar):
#   ''' test if character is 'close' according to tr29'''
#   if unichar == geresh:
#     return False
#   if unichar in stermlist:
#       return False
#   category = ud.category(unichar)
#   return category == "Pe" or category == "Ps" or unichar in lbqulist

picklefile = os.path.join(scriptdir, 'SentBreakHash.pickle')
ps = dict(pickle.load(open(picklefile, 'r')))

# table 4a macros
def ParaSep(char):
  return char in ps['Sep'] or char in ps['CR'] or char in ps['LF']

def SATerm(char):
  return char in ps['STerm'] or char in ps['ATerm']

def sbreak(input):
  ''' given a unicode string, return a list of unicode strings '''
  ret = []
  buffer = []
  # character goes in the buffer. if we break, then buffer goes in ret and is emptied
  for cn, char in enumerate(input):
    buffer.append(char)
    # SB3 : CR X LF
    if char in ps['CR'] and input[cn+1] in ps['LF']:
      continue
    # SB4 : ParaSep .-.
    if ParaSep(char):
      ret.append(''.join(buffer))
      buffer = []
      continue
    # SB5 is ignore rule; not sure what to do with it

def main():
  parser = argparse.ArgumentParser(description="Sentence break according to the unicode definition",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError, msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = gzip.open(args.infile.name, 'r') if args.infile.name.endswith(".gz") else args.infile
  infile = reader(infile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)

  buffer = []
  for line in infile:
    for 
    outfile.write(line)

if __name__ == '__main__':
  main()


import sys
import gzip
import random
import optparse
import copy
import pdb
import codecs
from operator import itemgetter
from collections import Counter # python >= 2.7

from c_segmenter import *
#from Counter import Counter

def smart_gzip_open(filename, *args):
    return gzip.open (filename, *args) if filename.endswith(".gz") else open (filename, *args)

def create_options_parser():
  usage = "usage: %prog -h/--help"
  p = optparse.OptionParser(usage)
  p.add_option("-b","--boundary",   dest="boundary",    help="BOUNDARY token", default="~~MORPHSYN_BOUNDARY~~")
  p.add_option("-c","--corpus",   dest="corpus",    help="corpus filename")
  p.add_option("-o","--outfile",   dest="outfile",    help="output dictionary")
  p.add_option("-i","--iters",  dest="numit",   help="number of ITERS", type="int", default=50)
  p.add_option("-t","--tags",  dest="num_tags",   help="number of TAGS", type="int", default=1)
  p.add_option("-r","--rseed",  dest="randseed",help="RANDdom SEED (default = 0)",type="int",default=0)
  p.add_option("--not-utf8",dest="utf8",help="input is *not* UTF8",default=True,action="store_false")
  p.add_option("--classes",dest="classes",help="expect class sequence in third position",default=False,action="store_true")
  p.add_option("-q","--seq",    dest="seq",     help="use sequential token model, i.e. #3", default=False, action="store_true")
  p.add_option("-a","--agreement", dest="agreement",     help="use agreement model, i.e. #4", default=False, action="store_true")
  p.add_option("-d","--dict",   dest="dict",    help="input dictionary (format: <filename>:[t][s][f]) t=use tag, s=use seg, f=freeze", action="append", default=[])

  return p

def read_corpus(filename, utf8, boundary):
    def parse_line (line):
        cols = line.strip().split('\t')
        assert len(cols) >= 2
        cols[0] = int (cols[0])
        cols[1] = tuple(cols[1].split())
        cols[2] = tuple(cols[2].split())
        return tuple(cols[0:3])
    rows = tuple([ parse_line (line.decode("utf-8") if utf8 else line)
                   for line in smart_gzip_open (filename) ])

    # remove consecutive boundary markers
    assert "".join(rows[0][1]) == boundary
    new_rows = []
    for i,row in enumerate(rows):
        if i == 0 or "".join(row[1]) != boundary:
            new_rows. append (row)
        elif "".join(rows[i-1][1]) != boundary:
            new_rows. append (row)
    rows = tuple(new_rows)
    return zip(*rows)

def count_word_types (counts, tokens, classes):
    assert len(counts) == len(tokens)
    assert len(tokens) == len(classes)
    wc = Counter()
    for count,token,cls in zip(counts,tokens, classes):
        if count < 0: continue
        to_segment = count > 0
        wc [(token,cls)] += 1 if to_segment else 0

    return tuple([ (w[0],c,w[1]) for w,c in sorted ( wc.iteritems(), key=lambda (w,c): w ) ])

def check_data (token_counts, tokens, boundary):
    assert len(token_counts) == len(tokens)
    for c,t in zip(token_counts,tokens):
        if t == boundary:
            assert c < 0

def check_dict (num_tags, input_dict):
    for (word,cls,tag,stem_index,compact_spans,init_seg,init_stem,init_tag,fix_seg,fix_stem,fix_tag) in input_dict:
        num_morphemes = len(compact_spans) + 1
        assert 0 <= stem_index < num_morphemes
        assert 0 <= tag
        assert cls == "#" or len(cls) == len(word)
        if init_tag: assert tag <= num_tags

def run_gibbs ( token_counts, tokens, classes, rand_seed, num_tags, numit,
                input_dictionary,
                seq,
                boundary,
                agreement):

    check_data (token_counts, tokens, boundary)
    check_dict (num_tags, input_dictionary)
    
    wordcounts = count_word_types (token_counts, tokens, classes)
    print "python: corpus has %d types" % len(wordcounts)

    return c_run_gibbs ( rand_seed, num_tags, numit, wordcounts,
                         input_dictionary,
                         tokens if seq else (),
                         classes if classes is not None else ("#",)*len(tokens), # needed?
                         boundary,
                         agreement
                         )

def dump_dict (outfile, word_states, utf8):
    for ws in word_states:
        if not ( ws.seg_frozen and ws.tag_frozen ):
            print >>outfile,"%s %s %d %d" % (ws.word,ws.cls,ws.tag,ws.stem_index),
            cs = ws.compact_spans
            starts = [ 0 ]
            starts. extend ( [ i for i in cs ] )
            ends = [ i for i in cs ]
            ends. append ( len(ws.word) )
            w = ws.word.decode("utf-8") if utf8 else ws.word
            for (start,end) in zip(starts,ends):
                morpheme = w[start:end].encode("utf-8") if utf8 else w[start:end]
                print >>outfile,morpheme,
            print >>outfile,""

def read_dict (infile, utf8):
    def get_compact_spans(morphemes):
        x = []
        y = 0
        for i,m in enumerate(morphemes):
            if i == len(morphemes)-1: break
            y += len(m)
            x. append (y)
        return tuple(x)
            
    d = []
    for line in infile:
        if utf8:
            line = line.strip().decode("utf-8")
        else:
            line = line.strip()
        tokens = line.split()
        (word,cls,tag,stem_index) = tokens[:4]
        tag = int(tag)
        stem_index = int(stem_index)
        morphemes = tuple(tokens[4:])
        assert word == "".join(morphemes)
        s = get_compact_spans (morphemes)
        d. append (  (word,cls,tag,stem_index,s) )
    return tuple(d)

def enrich_dict ( input_dict,
                  init_segs, init_stem, init_tags,
                  fix_segs, fix_stem, fix_tags ):

    def enrich(entry, init_segs, init_stem, init_tags, fix_segs, fix_stem, fix_tags):
        r = list(entry)
        r. append (init_segs)
        r. append (init_stem)
        r. append (init_tags)
        r. append (fix_segs)
        r. append (fix_stem)
        r. append (fix_tags)
        return tuple(r)

    fields = ('word','class','tag','stem_index','spans','init_seg','init_stem','init_tag','fix_seg','fix_stem','fix_tag')
    names = dict( (f,i) for i,f in enumerate(fields) )
    return (names,tuple([ enrich (entry, init_segs, init_stem, init_tags, fix_segs, fix_stem, fix_tags)
                          for entry in input_dict ]))

def parse_and_import_dictionaries ( args, utf8 ):
    def decode_dict_arg(a):
        i = a.rfind (":")
        if (i >= 0):
            filename = a[:i]
            usage = a[i+1:]
            init_tags = 't' in usage
            init_stem = 's' in usage
            init_segs = 'm' in usage
            freeze_tags = 'T' in usage
            freeze_stem = 'S' in usage
            freeze_segs = 'M' in usage
            if init_stem: assert init_segs
            if freeze_stem: assert freeze_segs
        else:
            filename = a
            init_tags = True
            init_stem = True
            init_segs = True
            freeze_tags = False
            freeze_segs = False
            freeze_stem = False
        d = read_dict ( smart_gzip_open(filename), utf8 )
        return enrich_dict ( d, init_segs, init_stem, init_tags, freeze_segs, freeze_stem, freeze_tags )

    def merge_entry(e1, e2, names):
        assert type(e1) == tuple
        new_e = list(e1)
        for n1,n2 in zip(('init_tag','init_seg','init_stem'),
                         ('tag','spans','stem_index')):
            i = names[n1]
            if e2[i]:
                new_e[i] = e2[i]
                j = names[n2]
                new_e[j] = e2[j]
        for n1 in ('fix_tag','fix_seg','fix_stem'):
            i = names[n1]
            new_e[i] = e2[i]
        return tuple(new_e)
            
    retval = []
    w2e = {}
    for arg in args:
        (names,d) = decode_dict_arg(arg)
        for entry in d:
            w = entry[0]
            if w not in w2e:
                retval. append (entry)
                w2e [w] = len(retval)-1
            else:
                ind = w2e [w]
                e = retval [ ind ]
                #updated_entry = merge_entry (e, entry, names)
                #retval [ind] = updated_entry
                retval [ind] = e # overwrites completely
                
    return tuple(retval)

def main():
    # python2.6 run_segmenter.py  -c ~/research/data/ibm/delphi/tahyyes_2007q2.seq.fpg -i 10
    # python2.6 run_segmenter.py  -c /scratch/yklee/morph-data/atb.seq.fpg -i 10
    # time python2.6  run_segmenter.py  -c ~/research/data/ibm/delphi/tahyyes_2007q2.seq.fpg -t 1 -i 0 --utf8
    # python2.6 run_segmenter.py  -c atb -i 1 -t 1 -o /dev/null -d atb.dict -q
    parser = create_options_parser()
    (options,args) = parser.parse_args()

    random.seed (options.randseed)

    boundary = options.boundary.decode("utf-8") if options.utf8 else options.boundary
    print "python: boundary token =", boundary
    
    cols = read_corpus (options.corpus, options.utf8, boundary)
    counts = cols[0]
    tokens = tuple(map(lambda x : "".join(x), cols[1]))
    classes = tuple(map(lambda x : "".join(x), cols[2])) if options.classes else ("#",)*len(tokens)

    
    if options.utf8: print "python: using utf-8"
    for i in range(5):
        if len(tokens) > i:
            print "python: corpus token %d has length %d" % (i,len(tokens[i]))
    for i in range(-5,0):
        if len(tokens) > abs(i):
            print "python: corpus token %d has length %d" % (i,len(tokens[i]))


    input_dictionary = parse_and_import_dictionaries (options.dict, options.utf8)

    print "python: corpus has %d tokens (after removing repeated boundaries)" % len(tokens)
    print "python: input dictionaries have %d entries" % len(input_dictionary)
    word_states = run_gibbs ( counts, tokens, classes, options.randseed, options.num_tags, options.numit,
                              input_dictionary,
                              options.seq,
                              boundary,
                              options.agreement )
    #pdb.set_trace()
    if options.outfile:
        dump_dict (smart_gzip_open(options.outfile,'w'), word_states, options.utf8)
    else:
        dump_dict (sys.stdout, word_states)
    
if __name__ == '__main__':
    main()

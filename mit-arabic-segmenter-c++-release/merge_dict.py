import sys
import collections
#from Counter import Counter
from collections import Counter # python >= 2.7
import pdb

def update_segmentation_counter (seg_counts, infile, utf8):
    for line in infile:
        tokens = line.split()
        word = tokens.pop(0)
        if utf8:
            word = word.decode("UTF-8")
        tag = int (tokens.pop(0))
        stem_index = int (tokens.pop(0))
        morphemes = tuple(tokens)
        if utf8:
            morphemes = tuple([ m.decode("UTF-8") for m in morphemes ])
        assert "".join(morphemes) == word
        assert 0 <= stem_index < len(morphemes)
        #seg_counts [word] [ (stem_index,morphemes) ] += 1
        seg_counts [word] [ morphemes ] += 1

def main():
    seg_counts = collections.defaultdict (Counter)
    utf8 = True
    for filename in open(sys.argv[1]):
        update_segmentation_counter (seg_counts, open(filename.strip()), utf8=True)

    for (w,sc) in sorted(seg_counts.iteritems(), key=lambda (k,v) : k):
        (morphemes,count) = sc.most_common(1)[0]
        tag = 1 # meaningless
        stem_index = 0 # meaningless
        if True:
            if utf8:
                print w.encode("utf-8"),tag,stem_index," ".join(morphemes).encode("utf-8")
            else:
                print w,tag,stem_index," ".join(morphemes)
        else:
            if count > 1:
                print w,tag,stem_index," ".join(morphemes)
            else:
                # output not segmented with max count is one
                print w,tag,0,w
    
if __name__ == '__main__':
    # python2.6 merge_dict.py filelist_of_dictionaries > merged.dict
    main()

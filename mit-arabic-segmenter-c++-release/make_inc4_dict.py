import sys
import gzip
import pdb

def smart_gzip_open(filename, *args):
    return gzip.open(filename,*args) if filename.endswith(".gz") else open(filename,*args)

def read_dict (infile):
    def parse_line(line):
        t = line.strip().split()
        word = t[0]
        return (word,line.strip())
    entries = [ parse_line(line) for line in infile ]
    d = tuple(entries)
    words = set([ entry[0] for entry in entries ])
    return (d,words)

def combine(w,oldd,newd):
    tag = newd[w].split()[1]
    segs = oldd[w].split()[2:]
    retval = [ w,tag ]
    retval. extend ( segs )
    return (w," ".join(retval))

def write_dict (d, outfile):
    for entry in d:
        print >>outfile,entry[1]
            
if __name__ == '__main__':
    (old_dict,old_words) = read_dict ( smart_gzip_open(sys.argv[1]) )
    (new_dict,new_words) = read_dict ( smart_gzip_open(sys.argv[2]) )

    old_words_in_new_dict = set([ entry[0] for entry in new_dict if entry[0] in old_words ])

    # words in old_dict not in new dict: keep
    d1 = tuple([ entry for entry in old_dict if entry[0] not in old_words_in_new_dict ])

    # words in new_dict not in old dict; keep
    d2 = tuple([ entry for entry in new_dict if entry[0] not in  old_words_in_new_dict ])

    # words in new_dict in old_dict: use tag in new_dict, but segmentation in old_dict
    oldd = dict(old_dict)
    newd = dict(new_dict)
    d3 = tuple([ combine(word,oldd,newd) for word in old_words_in_new_dict ])
    assert len(d3) == len(old_words_in_new_dict)

    write_dict (d1, smart_gzip_open(sys.argv[3],'w'))
    write_dict (d2, smart_gzip_open(sys.argv[4],'w'))
    write_dict (d3, smart_gzip_open(sys.argv[5],'w'))

import sys

def main():
    """ input (stdin): one word token per line
        output (stdout): format required by my segmenter """

    # if words are too long, the machine may not have enough memory
    # set to -1 to segment all words
    #MAXLEN = 18
    MAXLEN = -1
    print >>sys.stderr,"segmenting all words.  if you run out of memory, set MAXLEN in convert_wordlist.py"

    print "\t".join ( ("-1", "~~", "#", "#") )
    for line in sys.stdin:
        word = line.decode("utf-8").strip().split()[0]
        if MAXLEN > 0 and len(word) > MAXLEN:
            print "\t".join ( ("0", word.encode("utf-8"), "#", "#") )
            print >>sys.stderr,"skipping word <%s> because it is too long" % word.encode("utf-8")
        else:
            print "\t".join ( ("1", word.encode("utf-8"), "#", "#") )
        print "\t".join ( ("-1", "~~", "#", "#") )

if __name__ == '__main__':
    main()

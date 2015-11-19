import sys
import pdb

def read_corpus ( infile ):
    def f(x):
        assert int(x[0]) == 1
        return tuple(x[1].split('-'))
        #return ( int(x[0]), tuple(x[1].split('-')) )
        
    corpus = [ line.strip().split() for line in infile if line.startswith("1") ]
    corpus = tuple(map(f, corpus))
    return corpus

def read_dict(infile):
    def f(line):
        x = line.strip().split()
        w = x[0]
        morphemes = tuple(x[3:])
        assert "".join(morphemes) == w
        return (w,morphemes)
    
    return dict([ f(line) for line in infile ])

def get_boundaries(m):
    assert len(m) > 0
    x = 0
    y = []
    for i,s in enumerate(m):
        if i == len(m)-1:
            break
        x += len(s)
        y. append(x)
    return set(y)

def score (corpus,d):
    total_gold = 0.
    total_predicted = 0.
    correct = 0.
    for gold in corpus:
        w = "".join(gold)
        prediction = d[w]

        gold_boundaries = get_boundaries(gold)
        predicted_boundaries = get_boundaries(prediction)

        #if len(gold_boundaries) > 1: pdb.set_trace()

        total_gold += len(gold_boundaries)
        total_predicted += len(predicted_boundaries)
        correct += len ( gold_boundaries & predicted_boundaries )

    assert total_gold > 0
    r = correct / total_gold
    p = correct / total_predicted if total_predicted > 0 else 0.
    f1 = 2 * r * p / ( r + p )
    return (r,p,f1,correct,total_gold,total_predicted)

if __name__ == '__main__':
    # python2.6 eval_dict.py ~/research/data/hoifung-naacl09/atb atb.dict 
    corpus_filename = sys.argv[1]
    dict_filename = sys.argv[2]

    corpus = read_corpus ( open(corpus_filename) )
    d = read_dict( open(dict_filename) )
    (r,p,f1,c,gg,pp) = score (corpus,d)
    print "r %5.3f p %5.3f f1 %5.3f correct %d gold %d predicted %d" % (r*100,p*100,f1*100,c,gg,pp)

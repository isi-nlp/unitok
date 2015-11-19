CXX = g++
#CXXFLAGS = -Wall -O0 -fPIC $(INCLUDES) -g -D_GLIBCXX_DEBUG
#CXXFLAGS = -Wall -O1 -fPIC $(INCLUDES) -g -lprofiler
CXXFLAGS = -Wall -O2 -fPIC $(INCLUDES) -g
#CXXFLAGS = -Wall -O2 -fPIC $(INCLUDES) -DBOOST_DISABLE_ASSERTS -DNDEBUG -lprofiler -ltcmalloc
#INCLUDES = -I "/usr/include/python2.6"
INCLUDES = -I "/usr/usc/python/2.7.8/include/python2.7"
LIBDIRS = -L "/usr/usc/python/2.7.8/lib/"
LDFLAGS = -lpython2.7 -lboost_python 
SOURCES = c_segmenter.cpp gibbs_sampler.hpp lexicon_state.hpp word_state.hpp utils.hpp nonzero_counter.hpp dirichlet_multinomial.hpp

all: c_segmenter.so

c_segmenter.so: c_segmenter.o
	g++ -shared -Wl,-soname,$@ $(LIBDIRS) -o $@ $< $(LDFLAGS)

c_segmenter.o: $(SOURCES)
	g++ $(CXXFLAGS) -c -o $@  c_segmenter.cpp

.PHONY: realclean
realclean:
	-rm *\.o *\.so *~

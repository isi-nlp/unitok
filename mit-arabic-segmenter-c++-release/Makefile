#CXX = g++
CXX = /opt/local/bin/g++-mp-4.9
#CXXFLAGS = -Wall -O0 -fPIC $(INCLUDES) -g -D_GLIBCXX_DEBUG
#CXXFLAGS = -Wall -O1 -fPIC $(INCLUDES) -g -lprofiler
CXXFLAGS = -Wall -O2 -fPIC $(INCLUDES) -g
#CXXFLAGS = -Wall -O2 -fPIC $(INCLUDES) -DBOOST_DISABLE_ASSERTS -DNDEBUG -lprofiler -ltcmalloc
INCLUDES = -I /usr/include/python2.7 -I /opt/local/include/boost
#INCLUDES = -I "/usr/usc/python/2.7.8/include/python2.7"
#LIBDIRS = -L "/usr/usc/python/2.7.8/lib/"
LIBDIRS = -L "/opt/local/lib"
LDFLAGS = -lpython2.7 -lboost_python 
SOURCES = c_segmenter.cpp gibbs_sampler.hpp lexicon_state.hpp word_state.hpp utils.hpp nonzero_counter.hpp dirichlet_multinomial.hpp

all: c_segmenter.so

c_segmenter.so: c_segmenter.o
  $(CXX) -shared -Wl,-install_name,$@, $(LIBDIRS) -o $@ $< $(LDFLAGS)
# linux
#	$(CXX) -shared -Wl,-soname,$@ $(LIBDIRS) -o $@ $< $(LDFLAGS)
# mac


c_segmenter.o: $(SOURCES)
	$(CXX) $(CXXFLAGS) -c -o $@  c_segmenter.cpp

.PHONY: realclean
realclean:
	-rm *\.o *\.so *~

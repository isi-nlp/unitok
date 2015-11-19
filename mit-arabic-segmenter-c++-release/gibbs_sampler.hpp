#ifndef MORPHSYN_GIBBS_SAMPLER_HPP
#define MORPHSYN_GIBBS_SAMPLER_HPP

#include <iostream>
#include <cassert>
#include <vector>
#include <limits>
#include <ext/numeric> // __gnu_cxx::iota
#include <algorithm> // random_shuffle
#include <tr1/unordered_map>
#include <boost/random.hpp>
#include <boost/bind.hpp>
#include <boost/tuple/tuple.hpp>
#include <boost/foreach.hpp>
#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>
#include <boost/lambda/lambda.hpp>
#include <boost/lambda/bind.hpp>

#include "lexicon_state.hpp"
#include "word_state.hpp"
#include "utils.hpp"

namespace bp = boost::python;

namespace morphsyn {

std::vector<boost::tuple<std::string,int> >
extract_word_type_counts(bp::tuple& type_counts)
{
  std::vector<boost::tuple<std::string,int> > v;
  v. reserve ( bp::len(type_counts) );

  bp::stl_input_iterator<bp::object> begin(type_counts), end;
  for(std::size_t i = 0 ; begin != end; ++begin,++i)
    {
      const bp::tuple& wc = bp::extract<bp::tuple> ( *begin );
      const std::string w = bp::extract<std::string> ( wc[0] );
      const int c = bp::extract<int> ( wc[1] );
      v. push_back ( boost::make_tuple ( w, c ) );
    }
  return v;
}

std::size_t calculate_word_state_space_size(const std::vector<std::vector<index_pair> >& all_possible_spans,
                                            const std::size_t num_tags)
{
  std::size_t count = 0;
  for(std::size_t s = 0; s < all_possible_spans.size(); ++s)
    {
      const std::size_t num_morphemes = all_possible_spans.size();
      for(std::size_t stem_index = 0; stem_index < num_morphemes; ++stem_index,++count)
        { }
    }
  count *= num_tags;
  return count;
}

std::pair<std::vector<double>, std::vector<boost::tuple<size_t,size_t,size_t> > >
get_sampling_logs ( const std::wstring& word,
                    const bool stem_frozen, const std::size_t frozen_stem_index,
                    const std::vector<std::vector<index_pair> >& all_possible_spans,
                    const std::vector<int>& all_possible_tags,
                    lexicon_state& state )
{
  using namespace std;

  // bypass std::make_pair which invokes copy constructors
  std::pair<std::vector<double>, std::vector<boost::tuple<size_t,size_t,size_t> > > retval;
  vector<double>& logprobs = retval.first;
  vector<boost::tuple<size_t,size_t,size_t> >& word_state_space = retval.second;

  const vector<double> log_tag_probs = state. calculate_log_tag_probs ( word, all_possible_tags );

  const size_t space_size = calculate_word_state_space_size (all_possible_spans, all_possible_tags.size());
  logprobs. reserve ( space_size );
  word_state_space. reserve ( space_size );

  for(size_t s = 0; s < all_possible_spans.size(); ++s)
    {
      const vector<index_pair>& spans = all_possible_spans [s];
      const size_t num_morphemes = all_possible_spans [s].size();
      for(size_t stem_index = 0; stem_index < num_morphemes; ++stem_index)
        {
          if (stem_frozen && stem_index != frozen_stem_index) continue;
            
          const vector<double> lp = state. log_unnorm_prob_of_word (word, 
                                                                    stem_index, 
                                                                    spans, 
                                                                    all_possible_tags, 
                                                                    log_tag_probs);

          assert (lp.size() == all_possible_tags.size());
          logprobs. insert ( logprobs.end(), lp.begin(), lp.end() );

          BOOST_FOREACH(const int tag, all_possible_tags)
            {
              word_state_space. push_back ( boost::make_tuple(s,stem_index,tag) );
            }
        }
    }

  assert ( word_state_space.size() == logprobs.size() );
          
  return retval;
}

static
std::vector<std::vector<index_pair> >
generate_possible_spans(const std::size_t word_len, 
                        const std::size_t max_spans, 
                        const bool frozen_spans,
                        const std::vector<index_pair>& given_spans)
{
  std::vector<std::vector<index_pair> > all_possible_spans;
  if (frozen_spans)
    {
      all_possible_spans. push_back (given_spans);
    }
  else
    {
      all_possible_spans = spans_up_to_length (word_len, max_spans);
    }
  return all_possible_spans;
}

static
std::vector<int> generate_possible_tags (const bool tag_frozen, 
                                         const int tag,
                                         const int NUM_TAGS)
{
  std::vector<int> v;
  if (tag_frozen)
    {
      v.push_back(tag);
    }
  else
    {
      v.resize(NUM_TAGS);
      __gnu_cxx::iota (v.begin(), v.end(), 1);
    }
  return v;
}

word_state sample_new_word_state ( dart_type& dart, lexicon_state& state, const word_state& ws )
{
  using namespace std;

  assert ( ws.removed );

  const size_t word_len = ws. word. size();
  const vector<vector<index_pair> > all_possible_spans = generate_possible_spans (word_len, state.MAX_SPANS,
                                                                                  ws.seg_frozen, ws.spans);
  assert (all_possible_spans.size() > 0);
  assert (ws.tag > 0);
  const vector<int> all_possible_tags = generate_possible_tags (ws.tag_frozen, ws.tag, state.NUM_TAGS);
  
  if (all_possible_spans.size() == 1 && all_possible_tags.size() == 1 && ws.stem_frozen)
    return word_state(ws);

  // start sample

  const pair<vector<double>, vector<boost::tuple<size_t,size_t,size_t> > >
    logs_and_space = get_sampling_logs ( ws.word,
                                         ws.stem_frozen, ws.stem_index,
                                         all_possible_spans,
                                         all_possible_tags,
                                         state );

  const vector<double>& logprobs = logs_and_space.first;
  const vector<boost::tuple<size_t,size_t,size_t> >& word_state_space = logs_and_space.second;
  const std::pair<size_t,double> sample = sample_from_logs (dart, logprobs);
  const size_t chosen = sample.first;
  // const double logz = sample.second;
  word_state new_ws(ws);

  new_ws. spans      =  all_possible_spans [ word_state_space [ chosen ]. get<0>() ];
  new_ws. stem_index =  word_state_space [ chosen ]. get<1>();
  new_ws. tag        =  word_state_space [ chosen ]. get<2>();

  return new_ws;
}

std::ostream& print_lexicon_stats(std::ostream& outs, const lexicon_state& state)
{
      const nonzero_counter<std::wstring> prefixes = state. affix_lexicon (word_state::prefix);
      const nonzero_counter<std::wstring> stems    = state. affix_lexicon (word_state::stem);
      const nonzero_counter<std::wstring> suffixes = state. affix_lexicon (word_state::suffix);
      outs << "+ " << prefixes.size() << ' '
           << "* " << stems.size() << ' '
           << "- " << suffixes.size() << ' ';
      return outs;
}

std::tr1::unordered_map<std::string,word_state> parse_input_dict (bp::tuple& input_d)
{
  std::tr1::unordered_map<std::string,word_state> d;

  bp::stl_input_iterator<bp::object> begin(input_d), end;
  for(std::size_t i = 0 ; begin != end; ++begin,++i)
    {
      const bp::tuple& entry = bp::extract<bp::tuple> ( *begin );
      const std::string w = bp::extract<std::string> ( entry[0] );
      const int tag = bp::extract<int> ( entry[1] );
      assert ( tag >= 0 );
      const int stem_index = bp::extract<int> ( entry[2] );
      assert ( stem_index >= 0 );
      const bp::tuple& compact_spans =  bp::extract<bp::tuple> ( entry[3] );
      const bool init_seg = bp::extract<bool> ( entry[4] );
      const bool init_stem = bp::extract<bool> ( entry[5] );
      const bool init_tag = bp::extract<bool> ( entry[6] );
      const bool freeze_seg = bp::extract<bool> ( entry[7] );
      const bool freeze_stem = bp::extract<bool> ( entry[8] );
      const bool freeze_tag = bp::extract<bool> ( entry[9] );

      word_state ws(w,0,tag);
      ws.stem_index = static_cast<std::size_t>(stem_index);
      
      // make spans from compact spans
      std::vector<std::size_t> cs;
      cs.reserve (bp::len(compact_spans));
      bp::stl_input_iterator<bp::object> begin2(compact_spans), end2;
      for( ; begin2 != end2; ++begin2)
        {
          const int s = bp::extract<int> ( *begin2 );
          assert ( s > 0 );
          assert ( s < static_cast<int>(ws.word.size()) );
          cs.push_back( static_cast<std::size_t>(s) );
        }
      std::vector<std::size_t> starts(1,0);
      starts.insert (starts.end(), cs.begin(), cs.end());
      std::vector<std::size_t> ends (cs.begin(), cs.end());
      ends.push_back ( ws.word.size() );
      assert (starts.size() == ends.size());
      std::vector<index_pair>& spans = ws.spans;
      spans.resize(0);
      spans.reserve(starts.size());
      for(std::size_t i = 0; i < starts.size(); ++i)
        {
          spans.push_back( std::make_pair(starts[i],ends[i]) );
        }

      // other attributes
      ws. seg_frozen = freeze_seg;
      ws. tag_frozen = freeze_tag;
      ws. stem_frozen = freeze_stem;

      if ( ! init_seg )
        ws. make_spans_invalid();
      if ( ! init_tag )
        ws. make_tag_invalid();
      if ( ! init_stem )
        ws. make_stem_invalid();
      
      d [w] = ws; // done
    }

  return d;
}

std::vector<std::wstring>
parse_tokens (bp::tuple& tokens_py)
{
  std::vector<std::wstring> tokens;
  tokens. reserve ( bp::len(tokens_py) );
  
  bp::stl_input_iterator<bp::object> begin(tokens_py), end;
  for(std::size_t i = 0 ; begin != end; ++begin,++i)
    {
      const std::string w = bp::extract<std::string> ( *begin );
      const std::wstring ww = widen_string(w);
      tokens. push_back (ww);
    }
  return tokens;
}

std::vector<word_state>
run_gibbs(const int random_seed,
          const int num_tags,
          const int numit,
          bp::tuple& word_types_counts,
          bp::tuple& input_d,
          bp::tuple& tokens_py,
          const std::string& boundary,
          const bool use_agreement
          )
{
  assert (num_tags > 0);
  assert (numit >= 0);

  rng_type rng (random_seed);
  boost::uniform_real<> zero_one(0,1);
  dart_type dart(rng, zero_one);

  std::cout << "C++: numit = " << numit << std::endl;
  const std::vector<boost::tuple<std::string,int> >
    v = extract_word_type_counts(word_types_counts);

  const std::tr1::unordered_map<std::string,word_state> 
    input_dict = parse_input_dict (input_d);

  const std::vector<std::wstring> tokens = parse_tokens (tokens_py);
  lexicon_state state(rng, v, num_tags, 
                      input_dict, 
                      tokens, widen_string(boundary), use_agreement
                      );

  std::vector<std::size_t> indices = state.non_frozen_indices();
  //std::vector<std::size_t> indices = std::vector<std::size_t> ( state.num_words() );
  //__gnu_cxx::iota (indices.begin(), indices.end(), 0);

  stl_rng shuffle_rng(rng);
  std::cout << "C++: non-frozen word types = " << indices.size() << std::endl;
  std::cout << "C++: iter = 0 ";
  print_lexicon_stats (std::cout, state);
  std::cout << std::endl;

  for(int iter = 1; iter <= numit; ++iter)
    {
      nonzero_counter<std::string> ops;
      std::random_shuffle (indices.begin(), indices.end(), shuffle_rng);
      BOOST_FOREACH(const std::size_t wid, indices)
        {
          const word_state& old_ws = state. remove_word (wid);
          const word_state new_ws = sample_new_word_state ( dart, state, old_ws );
          //const word_state new_ws(old_ws); // DEBUG
          ops. increment ( new_ws.diff_type(old_ws), 1 );
          state. add_word (wid, new_ws);
        }
      std::cout << "C++: iter  " << iter << ' ';
      if (iter == 1 || iter == numit) 
        {
          const bool ok = state. validate();
          std::cout << "validate " << ok << ' ';
          assert ( ok );
        }
      print_lexicon_stats (std::cout, state);
      std::cout << ops;
      std::cout << std::endl;
    }

  return state. dump_state();
}

} // namespace

#endif // MORPHSYN_GIBBS_SAMPLER_HPP

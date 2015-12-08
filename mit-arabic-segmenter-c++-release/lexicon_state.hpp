#ifndef MORPHSYN_LEXICON_STATE_HPP
#define MORPHSYN_LEXICON_STATE_HPP

#include <iostream>
#include <cassert>
#include <limits>
#include <vector>
#include <tr1/unordered_set>
#include <tr1/unordered_map>
#include <boost/utility.hpp> // noncopyable
#include <boost/foreach.hpp>
#include <boost/tuple/tuple.hpp>
#include <boost/multi_array.hpp>
#include <boost/random.hpp>
#include <boost/lambda/lambda.hpp>
#include <boost/lambda/bind.hpp>
#include <boost/assign/list_of.hpp>

#include "utf8.h"
#include "word_state.hpp"
#include "nonzero_counter.hpp"
#include "dirichlet_multinomial.hpp"


namespace morphsyn {

class lexicon_state : private boost::noncopyable {
public:
  const int MAX_SPANS;
  const int NUM_TAGS;
  const std::size_t MAX_AFFIXES;
  const int MODEL;
  const double ALPHA_TAG;
  const double ALPHA_SEG;
  const double ALPHA_TOK_EMIT;
  const double ALPHA_TOK_TRANSIT;
  const std::vector<double> X_GAMMA_NUM_UNIQUE_MORPHEMES;
  const double GAMMA_SEG_LEN;
  const double GAMMA_NUM_MORPHEMES_PER_WORD;
  const std::wstring BOUNDARY;
  const std::vector<double> SUFFIX_AGREEMENT_LOGPROB;

private:
  typedef boost::multi_array<morphsyn::word_state,1> word_state_array_type;
  typedef nonzero_counter<std::wstring> string_counter_type;
  typedef std::vector<string_counter_type> string_counters_type;
  typedef std::vector<fast_dirichlet_mult_array<std::wstring> > fast_dirichlet_mult_arrays_type;
  typedef std::tr1::unordered_map<std::wstring,std::vector<std::size_t> > word_locations_type;
  typedef std::tr1::unordered_map<std::wstring,std::size_t> word_index_map_type;
  const truncated_geom_distr NUM_MORPHEMES_PER_WORD_DISTR_;

  enum agreement_type { agreement_none, agreement_false, agreement_true, agreement_end };

  boost::mt19937& rng_;
  word_state_array_type words_;

  string_counter_type counter_seg_;
  string_counters_type x_counter_seg_;
  fast_dirichlet_mult_arrays_type x_fast_distrs_seg_gt_;
  dirichlet_mult<int> distr_type_tag_;

  const std::vector<std::wstring>& tokens_;
  const std::vector<std::wstring>& classes_;

  const word_index_map_type word_index_;
  const word_locations_type word_locations_;

  fast_dirichlet_mult_array<std::wstring> fast_distrs_token_gt_;
  std::vector<fast_dirichlet_mult> distrs_transition_;

  static
  word_state_array_type make_word_states(const std::vector<boost::tuple<std::string,int,std::string> >& type_counts,
                                         const int num_tags,
                                         rng_type& rng,
                                         const std::tr1::unordered_map<std::string,word_state>& input_dict)
  {
    assert (num_tags > 0);
    boost::uniform_int<> one_to_T (1,num_tags); // 1, 2, .., num_tags
    boost::variate_generator<boost::mt19937&, boost::uniform_int<> >
      roll_die(rng, one_to_T);

    word_state_array_type v(boost::extents[ type_counts.size() ]);
    std::cout << "C++: type-counts " << type_counts.size() << std::endl;
    for(std::size_t i = 0; i < type_counts.size(); ++i)
      {
        const std::string& w = type_counts [i]. get<0>();
        std::tr1::unordered_map<std::string,word_state>::const_iterator it = input_dict.find(w);

        const int c = type_counts [i]. get<1>();
        const std::string& cls = type_counts [i]. get<2>();
        const int tag = num_tags > 1 ? roll_die() : 1;
        word_state ws (w, c, cls, tag);
        if (it != input_dict.end())
          {
            word_state ws_in_dict = it->second;

            if (c > 0)
              {
                // copy from dictionary
                ws. seg_frozen = ws_in_dict. seg_frozen;
                ws. tag_frozen = ws_in_dict. tag_frozen;
                ws. stem_frozen = ws_in_dict. stem_frozen;
              }

            // initialize stem_index, spans, and tag if indicated

            if (ws_in_dict. valid_stem())
              {
                ws. stem_index = ws_in_dict. stem_index;
              }

            if (ws_in_dict. valid_spans())
              {
                ws. spans = ws_in_dict. spans;
              }

            if (ws_in_dict. valid_tag())
              {
                ws. tag = ws_in_dict. tag;
              }
          }

        v [i] = ws;
      }
        
    return v;
  }

  static
  word_index_map_type
  make_word_index(const word_state_array_type& words)
  {
    word_index_map_type w2id;
    for(std::size_t i = 0; i < words.size(); ++i)
      {
        w2id [words[i].word] = i;
      }
    return w2id;
  }

  static
  word_locations_type
  get_word_locations(const std::vector<std::wstring>& tokens,
                     const word_state_array_type& words,
                     const word_index_map_type& w2id)
  {
    word_locations_type locs;
    for(std::size_t i = 0; i < tokens.size(); ++i)
      {
        const std::wstring& tok = tokens[i];
        word_index_map_type::const_iterator it = w2id.find (tok);
        if (it != w2id.end())
          {
            locs [ tok ]. push_back (i);
          }
      }
    return locs;
  }

  boost::tuple<fast_dirichlet_mult_array<std::wstring>, std::vector<fast_dirichlet_mult> >
  get_token_counts() const
  {
    boost::tuple<fast_dirichlet_mult_array<std::wstring>, std::vector<fast_dirichlet_mult> >
      retval ( fast_dirichlet_mult_array<std::wstring>(ALPHA_TOK_EMIT, NUM_TAGS+1),
               std::vector<fast_dirichlet_mult>(NUM_TAGS+1, fast_dirichlet_mult(ALPHA_TOK_TRANSIT, NUM_TAGS+1))
               );
    fast_dirichlet_mult_array<std::wstring>& fast_distrs_token_gt = retval.get<0>();
    std::vector<fast_dirichlet_mult>& distrs_transition = retval.get<1>();
    
    std::tr1::unordered_map<std::wstring,std::size_t> w2ind;
    for(std::size_t i = 0; i < words_.size(); ++i)
      {
        w2ind [ words_[i].word ] = i;
      }

    for(std::size_t i = 0; i < tokens_.size(); ++i)
      {
        if ( i == 0 ) continue;
        const std::wstring& w = tokens_ [i];
        std::tr1::unordered_map<std::wstring,std::size_t>::const_iterator it;
        std::size_t t = 0;
        if (w != BOUNDARY)
          {
            it = w2ind.find(w);
            assert (it != w2ind.end());
            t = words_ [ it->second ]. tag;
          }
        if ( w != BOUNDARY)
          {
            fast_distrs_token_gt. observe (t, w, 1);
          }
        const std::wstring& w_ = tokens_ [i-1];
        std::size_t t_ = 0;
        if (w_ != BOUNDARY)
          {
            it = w2ind.find(w_);
            assert (it != w2ind.end());
            t_ = words_ [ it->second ]. tag;
          }
        distrs_transition [t_]. observe (t, 1);
      }
    return retval;
  }

  int get_model_number(const int num_tags, const std::vector<std::wstring>& tokens, const bool use_agreement) 
  {
    if (use_agreement)
      {
        assert ( ! tokens.empty() );
        return 4;
      }
    else if ( ! tokens.empty() )
      {
        return 3;
      }
    else
      {
        return num_tags > 1 ? 2 : 1;
      }
  }

  static
  std::vector<double> make_agreement_params()
  {
    std::vector<double> v(agreement_end);
    v [agreement_none] = std::log(0.3);
    v [agreement_false] = std::log(0.1);
    v [agreement_true] = std::log(0.6);
    return v;
  }

public:
  
  lexicon_state(boost::mt19937& rng,
                const std::vector<boost::tuple<std::string,int,std::string> >& type_counts,
                const int num_tags,
                const std::tr1::unordered_map<std::string,word_state>& input_dict,
                const std::vector<std::wstring>& tokens,
                const std::vector<std::wstring>& classes,
                const std::wstring& boundary,
                const bool use_agreement)
    : 
    MAX_SPANS (5),
    NUM_TAGS (num_tags),
    MAX_AFFIXES (2),
    MODEL ( get_model_number(num_tags, tokens, use_agreement) ), // JM TODO: consider classes
    ALPHA_TAG (0.1),
    ALPHA_SEG (0.1),
    ALPHA_TOK_EMIT (1e-5),
    ALPHA_TOK_TRANSIT (1.0),
    X_GAMMA_NUM_UNIQUE_MORPHEMES (make_gammas()),
    GAMMA_SEG_LEN (1.0/2),
    GAMMA_NUM_MORPHEMES_PER_WORD (1.0/4),
    BOUNDARY (boundary),
    SUFFIX_AGREEMENT_LOGPROB (make_agreement_params()),

    NUM_MORPHEMES_PER_WORD_DISTR_ (truncated_geom_distr(GAMMA_NUM_MORPHEMES_PER_WORD,MAX_SPANS)),

    rng_ (rng),
    words_ ( make_word_states (type_counts, num_tags, rng_, input_dict) ),

    distr_type_tag_ (ALPHA_TAG),

    tokens_ (tokens),
    classes_ (classes),
    word_index_ ( make_word_index(words_) ),
    word_locations_ ( get_word_locations(tokens, words_, word_index_) ), // JM TODO: consider classes
    fast_distrs_token_gt_(ALPHA_TOK_EMIT, NUM_TAGS+1)
  {
    std::cout << "C++: MODEL = " << MODEL << std::endl;
    boost::tie (counter_seg_, x_counter_seg_, x_fast_distrs_seg_gt_, distr_type_tag_) 
      = get_counts();
    
    boost::tie (fast_distrs_token_gt_, distrs_transition_)
      = get_token_counts();
  }

  static
  std::vector<double> make_gammas()
  {
    std::vector<double> v = boost::assign::list_of (1.0/1.1) (1.0/10000) (1.0/1.1);
    return v;
  }

  boost::tuple<string_counter_type,
               string_counters_type,
               fast_dirichlet_mult_arrays_type,
               dirichlet_mult<int> >
  get_counts() const
  {
    string_counter_type counter_seg;
    string_counters_type x_counter_seg(3);
    fast_dirichlet_mult_arrays_type x_fast_distrs_seg_gt(3, fast_dirichlet_mult_arrays_type::value_type(ALPHA_SEG, NUM_TAGS+1));
    dirichlet_mult<int> distr_type_tag(ALPHA_TAG);

    BOOST_FOREACH (const word_state& ws, words_)
      {
        distr_type_tag. observe (ws.tag, 1);
        if ( ws.count_seg )
          {
            const std::vector<std::wstring> morphemes = ws. get_morphemes ();
            for(std::size_t i = 0; i < morphemes.size(); ++i)
              {
                const std::wstring& morpheme = morphemes[i];
                counter_seg. increment (morpheme, 1);
                const word_state::affix_type atype = ws. affix_type_of_index (i);
                x_fast_distrs_seg_gt [atype]. observe (ws.tag, morpheme, 1);
                x_counter_seg [atype]. increment (morpheme, 1);
              }
          }
      }

    return boost::make_tuple(counter_seg, x_counter_seg, x_fast_distrs_seg_gt, distr_type_tag);
    
  }

  std::size_t num_words() const
  {
    return words_.size();
  }

  const word_state& peek_word (const std::size_t wid)
  {
    return words_ [wid];
  }

  void observe_word_state(const word_state& ws, const int count)
  {
    distr_type_tag_. observe (ws.tag, count);
    if ( ws.count_seg )
      {
        const std::vector<std::wstring> morphemes = ws. get_morphemes();
        for(std::size_t i = 0; i < morphemes.size(); ++i)
          {
            const std::wstring& m = morphemes[i];
            counter_seg_. increment (m, count);
            word_state::affix_type a = ws. affix_type_of_index (i);
            x_counter_seg_ [a]. increment (m, count);
            x_fast_distrs_seg_gt_ [a]. observe ( ws.tag, m, count );
          }
      }
    // JM TODO consider classes
    if ( ! tokens_.empty() )
      observe_word_state_from_tokens(ws, count);
  }

  void observe_word_state_from_tokens(const word_state& ws, const int count)
  {
    const std::wstring& w = ws.word;
    const int t = ws.tag;
    assert ( w != BOUNDARY );
    word_locations_type::const_iterator it = word_locations_.find(w);
    assert (it != word_locations_.end());
    BOOST_FOREACH(const std::size_t i, it->second)
      {
        //assert (tokens_[i] == w); // DEBUG
        fast_distrs_token_gt_.observe(t, w, count);

        const std::wstring& w_ = tokens_[i-1];
        int t_ = 0;
        if (w_ == BOUNDARY)
          t_ = 0;
        else if (w_ == w)
          t_ = t;
        else
          {
            const word_index_map_type::const_iterator wit = word_index_.find(w_);
            assert (wit != word_index_.end() );
            t_ = words_[ wit->second ].tag;
          }

        distrs_transition_[t_].observe(t, count);

        const std::wstring& _w = tokens_[i+1];
        if (_w != w)
          {
            int _t = 0;
            if (_w == BOUNDARY)
              _t = 0;
            else if (_w == w)
              {
                assert (false);
                _t = t;
              }
            else
              {
                const word_index_map_type::const_iterator wit = word_index_.find(_w);
                assert (wit != word_index_.end() );
                _t = words_[ wit->second ].tag;
              }
            distrs_transition_[t].observe(_t, count);
          }
      }
  }

  const word_state& remove_word (const std::size_t wid)
  {
    word_state& ws = words_ [wid];
    assert ( ws.tag > 0 );
    ws. removed = true;
    observe_word_state (ws, -1);
    return ws;
  }

  void add_word(const std::size_t wid, const word_state& ws)
  {
    assert ( words_[wid].word == ws.word );
    assert ( ws.tag > 0 );
    words_[wid] = ws;
    words_[wid]. removed = false;
    observe_word_state (ws, 1);
  }

  bool validate() const
  {
    const bool
      nothing_removed = words_.end() == std::find_if ( words_.begin(), words_.end(), boost::bind(&word_state::removed, _1) );

    string_counter_type counter_seg;
    string_counters_type x_counter_seg;
    fast_dirichlet_mult_arrays_type x_fast_distrs_seg_gt;
    dirichlet_mult<int> distr_type_tag (ALPHA_TAG);

    boost::tie (counter_seg, x_counter_seg, x_fast_distrs_seg_gt, distr_type_tag) 
      = get_counts();

    const bool counter_seg_match = counter_seg == counter_seg_;
    const bool x_counter_seg_match = x_counter_seg == x_counter_seg_;
    const bool x_fast_distrs_seg_gt_match = x_fast_distrs_seg_gt == x_fast_distrs_seg_gt_;
    const bool distr_type_tag_match =  distr_type_tag ==  distr_type_tag_;

    bool fast_distrs_token_gt_match = true;
    bool distrs_transition_match = true;
    if ( ! tokens_.empty() )
      {
        fast_dirichlet_mult_array<std::wstring> fast_distrs_token_gt(ALPHA_TOK_EMIT, NUM_TAGS+1);
        std::vector<fast_dirichlet_mult> distrs_transition;
        boost::tie (fast_distrs_token_gt, distrs_transition)
          = get_token_counts();
        fast_distrs_token_gt_match = fast_distrs_token_gt == fast_distrs_token_gt_;
        distrs_transition_match = distrs_transition == distrs_transition_;
      }

    return nothing_removed 
      && counter_seg_match
      && x_counter_seg_match
      && x_fast_distrs_seg_gt_match
      && distr_type_tag_match
      && fast_distrs_token_gt_match
      && distrs_transition_match

      ;
  }
  
  std::vector<std::size_t> non_frozen_indices() const
  {
    std::vector<std::size_t> v;
    v.reserve (words_.size());
    for(std::size_t i = 0; i < words_.size(); ++i)
      {
        if (NUM_TAGS > 1)
          {
            if ( ! words_[i].totally_frozen() )
              v. push_back (i);
          }
        else
          {
            if ( ! words_[i].seg_frozen )
              v. push_back (i);
          }
      }
    return v;
  }
  
  static
  bool stem_length_violated(const std::vector<index_pair>& spans, 
                            const std::size_t stem_index)
  {
    assert ( 0 <= stem_index );
    assert ( stem_index < spans.size() );

    const std::size_t stem_length = spans[stem_index].second - spans[stem_index].first;

    for(std::size_t i = 0; i < spans.size(); ++i)
      {
        if (i == stem_index) continue;
        const std::size_t morpheme_length = spans[i].second - spans[i].first;
        if (morpheme_length >= stem_length)
          return true;
      }
    return false;
  }

  nonzero_counter<std::wstring> affix_lexicon(const word_state::affix_type atype) const
  {
    nonzero_counter<std::wstring> lex;
    BOOST_FOREACH (const word_state& ws, words_)
      {
        const std::vector<std::wstring> morphemes = ws.get_morphemes();
        for(std::size_t i = 0; i < morphemes.size(); ++i)
          {
            const word_state::affix_type a = ws. affix_type_of_index(i);
            if (a == atype)
              lex. increment ( morphemes[i], 1 );
          }
      }
    return lex;
  }

  std::vector<double> calculate_log_tag_prior(const std::vector<int>& tags) const
  {
    std::vector<double> v;
    v. reserve( tags.size() );
    BOOST_FOREACH(const int t, tags)
      {
        v. push_back ( distr_type_tag_. log_prob (t, NUM_TAGS) );
      }
    return v;
  }

  std::vector<double> calculate_log_token_emission(const std::wstring& word,
                                                   const std::vector<int>& tags) const
  {
    const fast_dirichlet_mult_array<std::wstring>& d = fast_distrs_token_gt_;
    assert ( word != BOUNDARY );
    assert ( ! d.present (word) );
    
    word_locations_type::const_iterator it = word_locations_.find(word);
    assert (it != word_locations_.end());
    const std::size_t nw = it-> second. size();
    const std::size_t V = d.vocab_size();
    std::vector<double> retval (tags.size());
    for (std::size_t j = 0; j < tags.size(); ++j)
      {
        assert ( tags[j] > 0 );
        const std::size_t tag = static_cast<std::size_t> (tags[j]);
        const int total = d. total_for_index (tag);
        assert (total >= 0);
        for (std::size_t i = 0; i < nw; ++i)
          {
            const double numer = d.alpha() + i;
            const double denom = d.alpha() * V + total + i ;
            retval [j] += std::log ( numer / denom );
          }
      }
    return retval;
  }

  bool word_in_index(const std::wstring& w) const
  {
    word_index_map_type::const_iterator it = word_index_.find(w);
    return it != word_index_.end();
  }

  const word_state& get_word_state(const std::wstring& w) const
  {
    word_index_map_type::const_iterator it = word_index_.find(w);
    assert (it != word_index_.end());
    return words_[ it->second];
  }

  std::vector<double> calculate_log_token_transition(const std::wstring& word,
                                                     const std::vector<int>& tags) const
  {
    assert ( word != BOUNDARY );
    //boost::multi_array<std::size_t,3> counts (boost::extents[NUM_TAGS+1][NUM_TAGS+1][NUM_TAGS+1]);
    std::tr1::unordered_map<int,std::tr1::unordered_map<int,std::tr1::unordered_map<int,std::size_t> > > counts;
    word_locations_type::const_iterator it = word_locations_.find(word);
    assert ( it != word_locations_.end() );
    BOOST_FOREACH ( const std::size_t i, it->second )
      {
        const std::wstring& w_ = tokens_[i-1];
        int t_;
        if (w_ == BOUNDARY)
          t_ = 0;
        else if (w_ == word)
          t_ = -1;
        else
          {
            t_ = get_word_state(w_).tag;
          }
        BOOST_FOREACH(const std::size_t t, tags)
          {
            if (t_ == -1)
              ++counts[t][t][t];
            else
              ++counts[t][t_][t];
          }
        
        const std::wstring& _w = tokens_[i+1];
        int _t;
        if (_w == BOUNDARY)
          _t = 0;
        else if (_w == word)
          _t = -1;
        else
          {
            _t = get_word_state(_w).tag;
          }
        BOOST_FOREACH(const std::size_t t, tags)
          {
            if (_t == -1)
              ++counts[t][t][t];
            else
              ++counts[t][t][_t];
          }
      }

    std::vector<double> logprobs(tags.size());
    for(std::size_t j = 0; j < tags.size(); ++j)
      {
        const int tag = tags[j];
        assert ( counts.find(tag) != counts.end() );
        typedef std::tr1::unordered_map<int,std::tr1::unordered_map<int,std::size_t> >::value_type value_type;
        std::tr1::unordered_map<int,std::tr1::unordered_map<int,std::tr1::unordered_map<int,std::size_t> > >::const_iterator it = counts.find(tag);
        assert ( it != counts.end() );
        BOOST_FOREACH(const value_type& value, it->second)
          {
            const int t_ = value.first;
            const fast_dirichlet_mult& d = distrs_transition_[t_];
            const std::size_t N = t_ == 0 ? NUM_TAGS : NUM_TAGS+1;
            int total = d.total();
            typedef std::tr1::unordered_map<int,std::size_t>::value_type value_type2;
            BOOST_FOREACH(const value_type2& value2, value.second)
              {
                const int t = value2.first;
                const std::size_t n = value2.second;
                const int count = d.counts(t);
                for(std::size_t i = 0; i < n; ++i)
                  {
                    const double numer = d.alpha() + count + i;
                    const double denom = d.alpha() + N + total + i;
                    logprobs[j] += std::log ( numer / denom );
                  }
                total += n;
              }
          }
      }
    return logprobs;
  }

  std::vector<double> calculate_hmm_log_probs (const std::wstring& word,
                                               const std::vector<int>& tags) const
  {
    const std::vector<double> log_emission_probs = calculate_log_token_emission(word,tags);
    assert (log_emission_probs.size() == tags.size());
    const std::vector<double> log_transition_probs = calculate_log_token_transition(word,tags);
    assert (log_transition_probs.size() == tags.size());

    std::vector<double> retval (log_emission_probs);
    std::transform(retval.begin(), retval.end(), log_transition_probs.begin(),
                   retval.begin(),
                   boost::lambda::_1 + boost::lambda::_2);
    return retval;
  }

  std::vector<double> calculate_log_tag_probs(const std::wstring& word,
                                              const std::vector<int>& tags) const
  {
    std::vector<double> retval = calculate_log_tag_prior(tags);
    assert (retval.size() == tags.size());
    if (MODEL >= 3)
      {
        const std::vector<double> hmm_logprobs = calculate_hmm_log_probs (word,tags);
        assert (tags.size() == hmm_logprobs.size());
        std::transform (retval.begin(), retval.end(), hmm_logprobs.begin(),
                        retval.begin(),
                        boost::lambda::_1 + boost::lambda::_2);
      }
    return retval;
  }

  template<typename InputIter>
  std::vector<std::wstring> get_new_morphemes(InputIter first, InputIter last) const
  {
    std::vector<std::wstring> v;
    for(InputIter it = first; it != last; ++it)
      {
        if ( counter_seg_. query (*it) == 0 )
          v. push_back (*it);
      }
    return v;
  }

  std::vector<std::tr1::unordered_set<std::wstring> >
  get_new_morphemes_by_type (const std::vector<std::wstring>& morphemes, const std::size_t stem_index ) const
  {
    std::vector<std::tr1::unordered_set<std::wstring> > affixes (word_state::end_);
    for(size_t i = 0; i < morphemes.size(); ++i)
      {
        const std::wstring& morpheme = morphemes[i];
        const word_state::affix_type atype = word_state::affix_type_of_index (i, stem_index);
        affixes [atype]. insert (morpheme);
      }    

    std::vector<std::tr1::unordered_set<std::wstring> > v(word_state::end_);
    for(std::size_t atype = 0; atype < affixes.size(); ++atype)
      {
        BOOST_FOREACH(const std::wstring& m, affixes[atype])
          {
            if (x_counter_seg_[atype]. query (m) == 0)
              v[atype].insert(m);
          }
      }
    return v;
  }

  double calculate_lexicon_size_logprobs ( const std::vector<std::tr1::unordered_set<std::wstring> >& new_unique_morphemes_by_type,
                                           const std::size_t min_num_morpheme_types,
                                           const std::vector<std::size_t>& min_vocab_sizes) const
  {
    double retval = 0;
    for(int i = 0; i != word_state::end_; ++i)
      {
        const word_state::affix_type a = static_cast<word_state::affix_type>(i);
        const std::size_t min_num_segs = x_counter_seg_[a].size() + new_unique_morphemes_by_type[a].size();
        assert ( min_num_segs == min_vocab_sizes[a] );
        retval += log_geometric ( X_GAMMA_NUM_UNIQUE_MORPHEMES[a], min_num_segs );
      }

    return retval;
  }

  double calculate_morpheme_length_logprobs ( const std::vector<std::wstring>& new_unique_morphemes ) const
  {
    double retval = 0;
    BOOST_FOREACH( const std::wstring& m, new_unique_morphemes)
      {
        retval += log_geometric (GAMMA_SEG_LEN, m.size()-1);
      }
    return retval;
  }
  
  double calculate_morphemes_per_word_logprobs ( const std::size_t k ) const
  {
    return NUM_MORPHEMES_PER_WORD_DISTR_.logprob (k);
  }

  std::vector<std::size_t> get_min_affix_vocab_size (const std::vector<std::tr1::unordered_set<std::wstring> >& new_unique_morphemes_by_type,
                                                     const std::size_t stem_index ) const
  {
    std::vector<std::size_t> retval;
    for(std::size_t atype = 0; atype < new_unique_morphemes_by_type.size(); ++atype)
      {
        const std::size_t current_size = x_counter_seg_[atype].size();
        std::size_t new_ones =  new_unique_morphemes_by_type[atype].size();
        BOOST_FOREACH(const std::wstring& m, new_unique_morphemes_by_type[atype])
          {
            assert (x_counter_seg_[atype]. query (m) == 0);
          }
        retval.push_back (current_size + new_ones);
      }
    return retval;
  }

  std::vector<double> calculate_surface_logprobs ( const std::vector<std::wstring>& morphemes, 
                                                   const std::size_t stem_index,
                                                   const std::vector<std::tr1::unordered_set<std::wstring> >& new_unique_morphemes_by_type,
                                                   const std::vector<int>& tags)
  {
    using namespace std;

    vector<double> retval(tags.size());

    //const vector<size_t> affix_min_vocab_size = get_min_affix_vocab_size (morphemes, stem_index);
    const vector<size_t> affix_min_vocab_size = get_min_affix_vocab_size (new_unique_morphemes_by_type, stem_index);
    for(size_t i = 0; i < morphemes.size(); ++i)
      {
        const wstring& morpheme = morphemes[i];
        const word_state::affix_type atype = word_state::affix_type_of_index (i, stem_index);
        fast_dirichlet_mult_array<wstring>& distr = x_fast_distrs_seg_gt_[atype];
        const size_t Ns = affix_min_vocab_size[atype];
        if (atype == word_state::stem)
          {
            const double v = distr. log_probs_no_tag (morpheme, Ns);
            transform (retval.begin(), retval.end(), retval.begin(),
                       boost::lambda::_1 + v);
          }
        else
          {
            const vector<double> p = distr. log_prob (morpheme, Ns);
            if ( ! (i+1 == stem_index || i == morphemes.size()-1) )
              {
                BOOST_FOREACH(const int tag, tags)
                  {
                    distr. observe(tag, morpheme, 1);
                  }
              }
            for(std::size_t tind = 0; tind < tags.size(); ++tind)
              {
                const int tag = tags [tind];
                assert (tag < static_cast<int>(p.size()));
                retval [tind] += p[tag];
              }
          }
      }

    // undo cascading counts
    for(size_t i = 0; i < morphemes.size(); ++i)
      {
        if (i == stem_index) continue;
        
        const wstring& morpheme = morphemes[i];
        const word_state::affix_type atype = word_state::affix_type_of_index (i, stem_index);
        fast_dirichlet_mult_array<wstring>& distr = x_fast_distrs_seg_gt_[atype];

        if ( ! (i+1 == stem_index || i == morphemes.size()-1) )
          {
            BOOST_FOREACH(const int tag, tags)
              {
                distr. observe(tag, morpheme, -1);
              }
          }
      }

    return retval;
  }

  agreement_type calculate_suffix_match(const std::wstring& w,
                                        const std::vector<index_pair>& spans,
                                        const std::size_t stem_index,
                                        const std::wstring& neighbor) const
  {
    assert (w != neighbor);
    word_index_map_type::const_iterator it = word_index_.find(neighbor);
    if (it == word_index_.end())
      {
        return agreement_none;
      }
    else
      {
        const std::wstring w_sfx = word_state::get_final_suffix (w,spans,stem_index);
        const std::wstring n_sfx = words_ [it->second]. get_final_suffix();
        const std::size_t m = std::max ( w_sfx.size(), n_sfx.size() );
        if (m > 0)
          {
            const std::size_t woffset = std::max ( 0, static_cast<int>(w.size() -m) );
            const std::size_t noffset = std::max ( 0, static_cast<int>(neighbor.size() -m) );
            if ( w.substr (woffset) == neighbor.substr (noffset) )
              return w_sfx == n_sfx ? agreement_true : agreement_false;
            else
              return agreement_none;
          }
        else
          {
            return agreement_none;
          }
      }
  }

  double calculate_pairwise_agreement_logprob ( const std::wstring& word, 
                                                const std::vector<index_pair>& spans,
                                                const std::size_t stem_index ) const
  {
    word_locations_type::const_iterator it = word_locations_.find(word);
    assert (it != word_locations_.end());
    double logprob = 0;
    BOOST_FOREACH (const std::size_t i, it->second)
      {
        const std::wstring& w_ = tokens_[i-1];
        if (word != w_)
          {
            const agreement_type suffix_match = calculate_suffix_match(word,spans,stem_index,w_);
            logprob += SUFFIX_AGREEMENT_LOGPROB [suffix_match];
          }
        else
          {
            logprob += SUFFIX_AGREEMENT_LOGPROB [agreement_true];
          }
        const std::wstring& _w = tokens_[i+1];
        if (word != _w)
          {
            const agreement_type suffix_match = calculate_suffix_match(word,spans,stem_index,_w);
            logprob += SUFFIX_AGREEMENT_LOGPROB [suffix_match];
          }
        else
          {
            logprob += SUFFIX_AGREEMENT_LOGPROB [agreement_true];
          }
      }
    return logprob;
  }

  std::vector<double> log_unnorm_prob_of_word(const std::wstring& word,
                                              const std::size_t stem_index,
                                              const std::vector<index_pair>& spans,
                                              const std::vector<int>& tags,
                                              const std::vector<double>& log_tag_probs)
  {
    assert ( stem_index < spans.size() );

    using namespace std;
    
    if (stem_index > MAX_AFFIXES || spans.size() - stem_index > MAX_AFFIXES+1)
      return vector<double> ( tags.size(), NEG_INF_DOUBLE );

    if (stem_length_violated (spans, stem_index))
      return vector<double> ( tags.size(), NEG_INF_DOUBLE );

    const vector<wstring> morphemes = word_state::get_morphemes (word, spans);
    const tr1::unordered_set<wstring> unique_morphemes ( morphemes.begin(), morphemes.end() );
    const vector<wstring> new_unique_morphemes = get_new_morphemes (unique_morphemes.begin(),unique_morphemes.end());
    
    const size_t min_num_morpheme_types = new_unique_morphemes.size() + counter_seg_.size();
    
    const vector<tr1::unordered_set<wstring> > new_unique_morphemes_by_type = get_new_morphemes_by_type ( morphemes, stem_index );

    const std::vector<std::size_t> min_vocab_sizes = get_min_affix_vocab_size (new_unique_morphemes_by_type, stem_index);

    double log_prob_lexicon = 0;
    
    log_prob_lexicon += calculate_lexicon_size_logprobs ( new_unique_morphemes_by_type,
                                                          min_num_morpheme_types,
                                                          min_vocab_sizes );
    log_prob_lexicon += calculate_morpheme_length_logprobs ( new_unique_morphemes );
    log_prob_lexicon += calculate_morphemes_per_word_logprobs ( spans.size() );

    vector<double> logprobs ( log_tag_probs );
    transform (logprobs.begin(), logprobs.end(), logprobs.begin(), boost::lambda::_1 + log_prob_lexicon );

    // surface forms
    const vector<double> 
      surface_logprobs = calculate_surface_logprobs ( morphemes, stem_index, new_unique_morphemes_by_type, tags );

    assert (surface_logprobs.size() == tags.size());
    transform (logprobs.begin(), logprobs.end(), 
               surface_logprobs.begin(), 
               logprobs.begin(), boost::lambda::_1 + boost::lambda::_2 );

    if ( MODEL == 4 )
      {
        const double ending_logprob = calculate_pairwise_agreement_logprob ( word, spans, stem_index );
        transform (logprobs.begin(), logprobs.end(), 
                   logprobs.begin(), boost::lambda::_1 + ending_logprob );
      }
    
    return vector<double> ( logprobs.begin(), logprobs.end());
  }

  //std::vector<boost::tuple<std::string,int,std::vector<int> > >
  std::vector<word_state>
  dump_state() const
  {
    std::vector<word_state > retval;
    retval. reserve (words_.size());

    BOOST_FOREACH (const word_state& ws, words_)
      {
        retval. push_back ( ws );
      }
    return retval;
  }

private:
}; // class lexicon_state

} // namespace

#endif // MORPHSYN_LEXICON_STATE_HPP

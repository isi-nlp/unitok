#ifndef MORPHSYN_WORD_STATE_HPP
#define MORPHSYN_WORD_STATE_HPP

#include <cassert>
#include <iostream>
#include <string>
#include <vector>
#include <utility>
#include <boost/foreach.hpp>
//#include <boost/utility.hpp> // noncopyable
//#include <boost/tuple/tuple.hpp>

#include "utils.hpp"

namespace morphsyn {

//class word_state : private boost::noncopyable {
class word_state {
public:
  enum affix_type { prefix, stem, suffix, end_ };

  static
  std::vector<index_pair> make_whole_word_span(const std::wstring& w)
  {
    std::vector<index_pair> v(1);
    v[0].first = 0;
    v[0].second = w.size();
    return v;
  }
public:
//private:
  std::string w_;
public:
  std::wstring word;
  bool removed;
  bool seg_frozen; // sample seg?
  bool stem_frozen; // sample stem_index?
  bool tag_frozen; // sample tag?
  bool count_seg; // don't use seg for statistics
  std::size_t tag;  // tag is always used for statistics
  std::size_t stem_index;
  std::vector<index_pair> spans;


  word_state () : removed(true) {}
  word_state (const std::string& w, const int c, const int t) :
    w_(w),
    word (morphsyn::widen_string(w)),
    removed (false), 
    seg_frozen (c <= 0),
    stem_frozen (false),
    tag_frozen (false),
    count_seg (true),
    tag (t),
    stem_index (0),
    spans ( make_whole_word_span(word) )
  {
    assert (tag > 0);
  }

  bool valid_stem() const
  {
    return stem_index < word.size();
  }

  bool valid_spans() const
  {
    return spans.size() > 0;
  }

  void make_stem_invalid()
  {
    stem_index = word.size() + 100;
  }

  void make_spans_invalid()
  {
    spans.clear();
  }

  bool valid_tag() const
  {
    return tag > 0;
  }

  void make_tag_invalid()
  {
    tag = 0;
  }

  std::vector<int> compact_spans() const
  {
    std::vector<int> v;
    for(int i = 0; i < static_cast<int>(spans.size()) -1; ++i)
      {
        v.push_back(spans[i].second);
      }
    return v;
  }

  bool totally_frozen() const
  {
    return seg_frozen && stem_frozen && tag_frozen;
  }

  bool operator==(const word_state& other) const
  {
    return w_ == other.w_
      && word == other.word
      && tag == other.tag
      && stem_index == other.stem_index
      && spans == other.spans
      && seg_frozen == other.seg_frozen
      && stem_frozen == other.stem_frozen
      && tag_frozen == other.tag_frozen
      && count_seg == other.count_seg
      && removed == other.removed;
  }
  bool operator!=(const word_state& other) const { return ! (*this == other); }

  std::ostream& display(std::ostream& os) const
  {
    os << w_ << " r " << removed 
       << " f " << seg_frozen << ' ' 
       << stem_frozen << ' ' 
       << tag_frozen << ' ' 
       << count_seg
       << " sz " << word.size() 
       << " tag " << tag << " stem " << stem_index << " spans " ;
    BOOST_FOREACH(const index_pair& span, spans)
      {
        os << span.first << ":" << span.second << ' ';
        //os << w_.substr(span.first, span.second-span.first) << ' ';
      }
    return os;
  }

  std::string diff_type(const word_state& other) const
  {
    const std::string tag_change = tag != other.tag ? "*" : "";
    const std::string stem_change = stem_index == other.stem_index ? ""
      : stem_index < other.stem_index ? "<" : ">";
    const std::string changes = tag_change + stem_change;
    if ( spans.size() > other.spans.size() )
      return changes + "split";
    else if ( spans.size() < other.spans.size() )
      return changes + "merge";
    else if ( spans.size() == other.spans.size() && changes.size() == 0 )
      return "noop";
    else
      return changes + "shuffle";
  }

  static
  std::wstring get_final_suffix(const std::wstring& w,
                                const std::vector<index_pair>& spans,
                                const std::size_t stem_index)
  {
    assert ( ! spans.empty() );
    if (stem_index < spans.size() -1)
      {
        const index_pair& s = spans[ spans.size()-1 ];
        return w.substr ( s.first );
      }
    else
      {
        return std::wstring(L"");
      }
  }

  std::wstring get_final_suffix() const
  {
    return get_final_suffix (word, spans, stem_index);
  }

  const std::string& utf8_word() const
  {
    return w_;
  }

  friend std::ostream&
  operator<<(std::ostream& os, const word_state& ws)
  {
    return ws.display(os);
  }

  static
  std::vector<std::wstring> get_morphemes(const std::wstring& s, 
                                          const std::vector<index_pair>& spans)
  {
    std::vector<std::wstring> m;
    m. reserve(spans.size());
    BOOST_FOREACH(const index_pair& span, spans)
      {
        assert ( span.first < span.second );
        m. push_back ( s.substr ( span.first, span.second-span.first) );
      }
    return m;
  }

  std::vector<std::wstring> get_morphemes() const
  {
    return get_morphemes (word, spans);
  }

  static
  affix_type affix_type_of_index (const std::size_t i, const std::size_t stem_index)
  {
    if (i < stem_index)
      return prefix;
    else if ( i == stem_index )
      return stem;
    else
      {
        return suffix;
      }
  }

  affix_type affix_type_of_index (const std::size_t i) const
  {
    assert (i < spans.size());
    return affix_type_of_index (i, stem_index);
  }
  
}; // class word_state

} // namespace

#endif // MORPHSYN_WORD_STATE_HPP

#ifndef MORPHSYN_NONZERO_COUNTER_HPP
#define MORPHSYN_NONZERO_COUNTER_HPP

#include <cassert>
#include <iostream>
#include <utility>
#include <vector>
//#include <tr1/unordered_map>
#include <boost/unordered_map.hpp>
#include <boost/foreach.hpp>
//#include <boost/utility.hpp> // noncopyable
#include <boost/bind.hpp>

namespace morphsyn {

template<typename K>
class nonzero_counter { // : private boost::noncopyable {
public:
  typedef K key_type;
  typedef int data_type;
  //typedef std::tr1::unordered_map<K,data_type> map_type;
  //typedef typename std::tr1::unordered_map<K,data_type>::iterator iterator;
  //typedef typename std::tr1::unordered_map<K,data_type>::const_iterator const_iterator;
  typedef boost::unordered_map<K,data_type> map_type;
  typedef typename boost::unordered_map<K,data_type>::iterator iterator;
  typedef typename boost::unordered_map<K,data_type>::const_iterator const_iterator;
private:
  map_type counts_;
public:
  nonzero_counter() {}
  
  bool operator==(const nonzero_counter<K>& other) const
  {
    return counts_ == other.counts_;
  }

  std::ostream& display(std::ostream& outs) const
  {
    typedef std::pair<K,data_type> map_value_type;
    std::vector<map_value_type> v ( counts_.begin(), counts_.end() );
    std::sort ( v.begin(), v.end(), 
                boost::bind(&map_value_type::second,_1) > boost::bind(&map_value_type::second,_2) );
     BOOST_FOREACH(const map_value_type& p, v)
       {
         outs << p.first << ":" << p.second << ' ';
       }
    return outs;
  }

  std::size_t size() const { return counts_.size(); }

  data_type query(key_type const& k) const
  {
    const_iterator it = counts_. find(k);
    if ( it == counts_.end() )
      return 0;
    else
      {
        assert ( it->second > 0 );
        return it->second;
      }
  }

  data_type increment(key_type const& k, const data_type count)
  {
    iterator it = counts_. find(k);
    if (it == counts_.end())
      {
        assert ( count > 0 );
        return counts_[k] = count;
      }
    else
      {
        it->second += count;
        assert ( it->second >= 0 );
        if ( it->second == 0 )
          {
            counts_. erase ( it );
            return 0;
          }
        else
          {
            return it->second;
          }
      }
  }

  std::ostream& display2(std::ostream& out) const
  {
    BOOST_FOREACH(typename map_type::value_type const& it, counts_)
      {
        out << it.first << ':' << it.second << ' ';
      }
    return out;
  }

  friend std::ostream& operator<<(std::ostream& out, const nonzero_counter& c)
  {
    return c.display(out);
  }
  
}; // class 

// template<typename K>
// inline
// bool operator==(const nonzero_counter<K>& a, const nonzero_counter<K>& b)
// {
//   return a.counts_ == b.counts_;
// }

} // namespace 

#endif // MORPHSYN_NONZERO_COUNTER_HPP

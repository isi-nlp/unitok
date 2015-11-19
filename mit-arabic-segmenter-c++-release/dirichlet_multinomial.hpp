#ifndef MORPHSYN_DIRICHLET_MULTINOMIAL_HPP
#define MORPHSYN_DIRICHLET_MULTINOMIAL_HPP

#include <cmath>
#include <cassert>
#include <numeric> // accumulate
//#include <tr1/unordered_map>
#include <boost/unordered_map.hpp>
#include <boost/multi_array.hpp>

#include "nonzero_counter.hpp"
#include "utils.hpp"

namespace morphsyn {

class fast_dirichlet_mult
{
private:
  typedef boost::multi_array<int,1> counter_type;
  double alpha_;
  std::size_t dim_;
  int total_;
  counter_type counts_;
public:
  fast_dirichlet_mult(const double alpha, const std::size_t dim)
    : alpha_(alpha),
      dim_(dim),
      total_(0),
      counts_ (boost::extents[dim])
  {
    assert (alpha >= 0);
  }
  
  void observe(const std::size_t key, const int count)
  {
    counts_ [key] += count;
    total_ += count;
    assert ( total_ >= 0 );
    assert ( counts_ [key] >= 0 );
  }

  bool operator==(const fast_dirichlet_mult& other) const
  {
    return alpha_ == other.alpha_
      && dim_ == other.dim_
      && total_ == other.total_
      && counts_ == other.counts_;
  }

  double alpha() const
  {
    return alpha_;
  }

  int total() const
  {
    return total_;
  }

  int counts(std::size_t i) const
  {
    return counts_[i];
  }

  double log_prob(const std::size_t key) const
  {
    return std::log ( ( alpha_ + counts_[key] ) / ( alpha_ * dim_ + total_ ) );
  }

  double log_prob_with_N(const std::size_t key, const std::size_t N) const
  {
    return std::log ( ( alpha_ + counts_[key] ) / ( alpha_ * N + total_ ) );
  }
}; // class fast_dirichlet_mult

template<typename T>
class dirichlet_mult
{
private:
  typedef nonzero_counter<T> counter_type;
  double alpha_;
  int total_;
  counter_type counts_;
public:
  dirichlet_mult(const double alpha)
    : alpha_(alpha),
      total_(0)
  {
    assert (alpha >= 0);
  }

  bool operator==(const dirichlet_mult& other) const
  {
    return alpha_ == other.alpha_
      && total_ == other.total_
      && counts_ == other.counts_
      ;
  }
  bool operator!=(const dirichlet_mult& other) const { return ! *this == other; }

  void observe(const T& key, int count)
  {
    counts_. increment (key, count);
    total_ += count;
  }

  std::size_t vocab_size() const
  {
    return counts_. size();
  }

  double prob(const T& key, std::size_t N) const
  {
    const double numer = alpha_ + counts_.query(key);
    const double denom = alpha_ * N + total_;
    return numer / denom;
  }

  double log_prob(const T& key, std::size_t N) const
  {
    return std::log (prob(key,N));
  }

}; // class dirichlet_multi

template<typename T>
class fast_dirichlet_mult_array
{
private:
  typedef boost::multi_array<int,1> count_type;
  //typedef std::tr1::unordered_map<T,count_type> map_type;
  typedef boost::unordered_map<T,count_type> map_type;
  double alpha_;
  std::size_t nd_;
  count_type totals_;
  map_type counts_;
public:
  fast_dirichlet_mult_array(const double alpha, const std::size_t num_distrs)
    : alpha_(alpha),
      nd_(num_distrs),
      totals_(boost::extents[num_distrs])
  { }

  bool operator==(const fast_dirichlet_mult_array<T>& other) const
  {
    return alpha_ == other.alpha_
      && nd_ == other.nd_
      && totals_ == other.totals_
      && counts_ == other.counts_;
  }

  double alpha() const
  {
    return alpha_;
  }

  bool present(const T& k) const
  {
    return counts_.find(k) != counts_.end();
  }

  int total_for_index(const std::size_t t) const
  {
    return totals_[t];
  }

  std::size_t vocab_size() const
  {
    return counts_.size();
  }

  void observe(const std::size_t i, const T& k, const std::size_t v)
  {
    typename map_type::iterator it = counts_.find(k);
    if (it == counts_.end())
      {
        counts_. insert ( typename map_type::value_type(k, count_type(boost::extents[nd_])) );
      }
    count_type& c = counts_[k];
    c[i] += v;
    totals_[i] += v;
    if ( c[i] == 0 && std::accumulate(c.begin(), c.end(), 0) == 0 )
      counts_.erase (k);
  }

  double log_probs_no_tag(const T& k, const std::size_t N) const
  {
    assert ( N > 0 );
    assert ( totals_[0] == 0 );
    const int sum_totals = std::accumulate(totals_.begin(), totals_.end(), 0);
    typename map_type::const_iterator it = counts_.find(k);
    if ( it != counts_.end() )
      {
        const count_type& countsk = it->second;
        assert ( countsk[0] == 0 );
        const int sum_counts = std::accumulate (countsk.begin(), countsk.end(), 0);
        return std::log ( ( alpha_ + sum_counts ) / ( alpha_ * N + sum_totals ) );
      }
    else
      {
        return std::log ( alpha_ / ( alpha_ * N + sum_totals ) );
      }
  }

  std::vector<double> log_prob(const T& k, const std::size_t N) const
  {
    assert (N > 0);
    std::vector<double> v (nd_);
    typename map_type::const_iterator it = counts_.find(k);
    if (it != counts_.end())
      {
        const count_type& countsk = it->second;
        assert ( countsk[0] == 0 );
        for(std::size_t i = 0; i < nd_; ++i)
          {
            v[i] = std::log ( ( alpha_ + countsk[i] ) / ( alpha_ * N + totals_[i] ) );
          }
      }
    else
      {
        for(std::size_t i = 0; i < nd_; ++i)
          {
            v[i] = std::log ( ( alpha_ ) / ( alpha_ * N + totals_[i] ) );
          }
      }
    return v;
  }

  std::vector<double> log_prob_with_Ns(const T& k, const std::vector<std::size_t>& Ns) const
  {
    assert ( Ns.size() == nd_ );
    std::vector<double> v (nd_);
    typename map_type::const_iterator it = counts_.find(k);
    if (it != counts_.end())
      {
        const count_type& countsk = it->second;
        assert ( countsk[0] == 0 );
        for(std::size_t i = 0; i < nd_; ++i)
          {
            assert (Ns[i] > 0);
            v[i] = std::log ( ( alpha_ + countsk[i] ) / ( alpha_ * Ns[i] + totals_[i] ) );
          }
      }
    else
      {
        for(std::size_t i = 0; i < nd_; ++i)
          {
            assert (Ns[i] > 0);
            v[i] = std::log ( ( alpha_ ) / ( alpha_ * Ns[i] + totals_[i] ) );
          }
      }
    return v;
  }
}; // class fast_dirichlet_mult_array

} // namespace

#endif // MORPHSYN_DIRICHLET_MULTINOMIAL_HPP

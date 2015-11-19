#ifndef MORPHSYN_UTILS_HPP
#define MORPHSYN_UTILS_HPP

#include <cmath>
#include <vector>
#include <utility>
#include <iterator> // distance
#include <algorithm>
#include <numeric>
#include <boost/foreach.hpp>
#include <boost/bind.hpp>
#include <boost/tuple/tuple.hpp>
#include <boost/random.hpp>
#include <boost/lambda/bind.hpp>
#include <boost/lambda/lambda.hpp>

#include "utf8.h"

namespace morphsyn {

typedef std::pair<std::size_t,std::size_t> index_pair;
typedef boost::mt19937 rng_type;
typedef boost::variate_generator<rng_type&, boost::uniform_real<> > dart_type;

const static double NEG_INF_DOUBLE = -std::numeric_limits<double>::infinity();

template<int N,typename T> inline
const typename boost::tuples::element<N,T>::type& tuple_at(const T& t)
{
  return boost::tuples::get<N>(t);
} 

template<typename T> inline
const T& vector_at(const std::vector<T>& v, const std::size_t i)
{
  return v[i];
} 


template<typename InputIter>
double logsumexp(InputIter first, InputIter last)
{
  if (first == last)
    return NEG_INF_DOUBLE;

  const double biggest = *std::max_element(first, last);
  return std::log( std::accumulate (first, last, 0.0,
                                    boost::lambda::_1 + boost::lambda::bind ( exp, boost::lambda::_2 - biggest )
                                    )) + biggest;
}

struct stl_rng : std::unary_function<unsigned, unsigned> {
  boost::mt19937 &_state;
  unsigned operator()(unsigned i) {
    boost::uniform_int<> rng(0, i - 1);
    return rng(_state);
  }
  stl_rng(boost::mt19937 &state) : _state(state) {}
};

double log_geometric(const double gamma, const int k)
{
  assert (k >= 0);
  return 1.0 * k * std::log (1.0-gamma) + std::log(gamma);
}

double log_geometric_truncated(const double gamma, const int k, const int N)
{
  assert (0 <= k);
  assert (k <= N);
  assert (N > 0);
  std::vector<double> v(N);
  for(int i = 0; i <= N; ++i)
    {
      v. push_back ( 1.0 * i * std::log(1.0-gamma) + std::log(gamma) );
    }
  const double b = *std::max_element(v.begin(), v.end());
  double logz = 0;
  BOOST_FOREACH(const double i, v)
    {
      logz += std::exp(i - b);
    }
  logz = std::log(logz);
  return v[k] - logz;
}

std::pair<std::size_t,double>
sample_from_logs (dart_type& dart, const std::vector<double>& logs)
{
  assert ( ! logs.empty() );

  const double logz = logsumexp (logs.begin(), logs.end());
  std::vector<double> probs ( logs.size() );  
  std::transform (logs.begin(), logs.end(),
                  probs.begin(),
                  boost::lambda::bind<double> (exp, boost::lambda::_1 - logz));
  assert ( std::fabs ( std::accumulate(probs.begin(), probs.end(), 0.0) - 1.0 ) < 0.1 );
  const double hit_zone = dart();
  assert ( hit_zone >= 0.0 );
  assert ( hit_zone < 1.0 );
  double sum = 0;
  for(std::size_t i = 0; i < probs.size(); ++i)  
    {
      sum += probs[i];
      if ( sum > hit_zone )
        return std::make_pair (i, logz);
    }
  assert (false);
  std::cout << "ERROR in sample_from_logs" << std::endl;
  return std::make_pair (0, logz);
}

std::wstring widen_string (const std::string& s)
{
  std::wstring ws;

  const size_t m = s.end() - s.begin();
  const char* const end = s.c_str() + m;
  
  for(const char* w = s.c_str(); w != end; )
    {
      unsigned p = utf8::next(w, end);
      ws += static_cast<wchar_t>(p);
    }
  return ws;
}

std::vector<std::vector<index_pair> > spans_of_length ( const std::size_t n, const std::size_t k )
{
  using namespace std;
  vector<vector<index_pair> > v;

  if (k > n)
    {
      return v;
    }
  else if (k == 1)
    {
      vector<index_pair> vv;
      vv. push_back ( make_pair(0,n) );
      v. push_back (vv);
      return v;
    }
  else
    {
      for(size_t split = 1; split < n; ++split)
        {
          vector<vector<index_pair> > spans = spans_of_length (n-split, k-1);
          BOOST_FOREACH( vector<index_pair>& span, spans)
            {
              BOOST_FOREACH( index_pair& p, span)
                {
                  p.first += split;
                  p.second += split;
                }
              span. push_back ( std::make_pair(0, split) );
              std::sort ( span.begin(), span.end(),
                          boost::bind(&index_pair::first, _1) < boost::bind(&index_pair::first, _2) );
              v. push_back (span);
            }
        }
      return v;
    }
}

std::vector<std::vector<index_pair> > spans_up_to_length (const size_t n, const size_t max_spans)
{
  std::vector<std::vector<index_pair> > v;
  for(std::size_t k = 1; k <= max_spans; ++k)
    {
      std::vector<std::vector<index_pair> > vv = spans_of_length(n, k);
      v. reserve ( v.size() + std::distance ( vv.begin(), vv.end() ) );
      v. insert ( v.end(), vv.begin(), vv.end() );
    }
  return v;
}

class truncated_geom_distr
{
private:
  const std::vector<double> logprobs_;
  const std::size_t N_;

  static
  std::vector<double> make_log_probs(const double gamma, const std::size_t N)
  {
    std::vector<double> v;
    for(std::size_t i = 0; i <= N; ++i)
      {
        v.push_back ( log_geometric(gamma,i) );
      }
    const double logz = logsumexp(v.begin(), v.end());
    std::transform (v.begin(), v.end(), v.begin(),
                    boost::lambda::_1 - logz);
    return v;
  }

public:
  truncated_geom_distr (const double gamma, const std::size_t N)
    : logprobs_ (make_log_probs(gamma,N)),
      N_ (N)
  { }

  double logprob(const std::size_t k) const
  {
    assert (k <= N_);
    return logprobs_[k];
  }
}; // class truncated_geom_distr

} // namespace morphsyn

#endif // MORPHSYN_UTILS_HPP

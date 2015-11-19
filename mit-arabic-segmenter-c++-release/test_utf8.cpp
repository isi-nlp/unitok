#include <cstdlib>
#include <string>
#include <iostream>
#include <cstring>
#include <tr1/unordered_map>

#include "utf8.h"

using namespace std;

int main(int argc, char* argv[])
{
  typedef tr1::unordered_map<wstring,int> map_type;
  map_type h;
  string line;

  while ( getline(cin, line) )
    {
      const size_t n = utf8::distance(line.begin(),line.end());
      const size_t m = line.end() - line.begin();
      const char* const end = line.c_str() + m;

      cout << "{" << line << "} "
           << "len(" << n << "/" << m << ")"
           << " ";

      const char* w = line.c_str();
      cout << "# " << w << " ";
      unsigned p = utf8::next(w, end);
      cout << w << ' ' << p
           << " $ ";

      //cout << sizeof(line.c_str()) << ' ' << strlen(line.c_str()) << ' ' << line.size() << endl;
      //continue;
      cout << "size(" << sizeof(line.c_str()) << ") ";
      wstring ws;
      for(const char* w = line.c_str(); w != end; )
        {
          const char* const w_old = w;
          unsigned p = utf8::next(w, end);
          cout << p << "(" << w-w_old << ")" << ' ';
          ws += static_cast<wchar_t>(p);
        }

      cout << ws.size() << " ";
      wstring ws2 = ws.substr(0,2);
      map_type::iterator it = h.find(ws2);
      if (it == h.end())
        h [ws2] = 1;
      else
        it->second += 1;
      for(wstring::iterator it = ws.begin(); it != ws.end(); ++it)
        {
          cout << *it << ' ';
        }
      
      cout << endl;
    }

  for(map_type::iterator it = h.begin(); it != h.end(); ++it)
    {
      cout << it->first[0] << ' ' << it->first[1] << ' ' << it->second << endl;
    }
  return 0;
}

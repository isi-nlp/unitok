#ifndef MORPHSYN_C_SEGMENTER_HPP
#define MORPHSYN_C_SEGMENTER_HPP

#include <vector>
#include <utility>
#include <boost/python.hpp>
#include <boost/python/module.hpp>
#include <boost/foreach.hpp>
//#include <boost/python/def.hpp>
//#include <boost/python/args.hpp>
#include <boost/tuple/tuple.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

//#include "tuple_conversion.h"

#include "word_state.hpp"
//#include "lexicon_state.hpp"
#include "gibbs_sampler.hpp"

using namespace boost::python;
//using namespace boost_adaptbx::tuple_conversion;

struct string_from_python_str
{
  string_from_python_str()
  {
    boost::python::converter::registry::push_back(
                                                  &convertible,
                                                  &construct,
                                                  boost::python::type_id<std::string>());
  }

  static void* convertible(PyObject* obj)
  {
    return
      (PyString_Check(obj) || PyUnicode_Check(obj)) 
      ? obj
      : 0
      ;
  }

  static void construct(
                        PyObject* obj,
                        boost::python::converter::rvalue_from_python_stage1_data* data)
  {
    namespace py = boost::python;
    if(PyString_Check(obj))
      {
        const char* value = PyString_AsString(obj);
        //MY_CHECK(value,translate("Received null string pointer from Python"));
        void* storage = ((py::converter::rvalue_from_python_storage<std::string>*)data)->storage.bytes;
        new (storage) std::string(value);
        data->convertible = storage;
      }
    else if(PyUnicode_Check(obj))
      {
        py::handle<> utf8(py::allow_null(PyUnicode_AsUTF8String(obj)));
        //MY_CHECK(utf8,translate("Could not convert Python unicode object to UTF8 string"));
        void* storage = ((py::converter::rvalue_from_python_storage<std::string>*)data)->storage.bytes;
        const char* utf8v = PyString_AsString(utf8.get());
        //MY_CHECK(utf8v,translate("Received null string from utf8 string"));
        new(storage) std::string(utf8v);
        data->convertible = storage;
      }
    else
      {
        ;//error(translate("Unexpected type for string conversion"));
      }
  }
};


BOOST_PYTHON_MODULE(c_segmenter)
{
  def("c_run_gibbs",  morphsyn::run_gibbs);
  
  class_<morphsyn::word_state>("WordState", init<>() )
    .def_readonly("word",&morphsyn::word_state::w_)
    .def_readwrite("tag",&morphsyn::word_state::tag)
    .def_readwrite("stem_index",&morphsyn::word_state::stem_index)
    .def_readwrite("seg_frozen",&morphsyn::word_state::seg_frozen)
    .def_readwrite("stem_frozen",&morphsyn::word_state::stem_frozen)
    .def_readwrite("tag_frozen",&morphsyn::word_state::tag_frozen)
    .def_readwrite("count_seg",&morphsyn::word_state::count_seg)
    .add_property("compact_spans",&morphsyn::word_state::compact_spans)
    ;
  
  class_<std::vector<int> >("IntVec")
    .def(bp::vector_indexing_suite<std::vector<int> >())
    ;

  class_<std::vector<morphsyn::word_state> >("WordStateVec")
    .def(bp::vector_indexing_suite<std::vector<morphsyn::word_state> >());
  ;

  //to_python<boost::tuple<std::string, int, std::vector<int> > >();
  string_from_python_str();
}

#endif // MORPHSYN_C_SEGMENTER_HPP

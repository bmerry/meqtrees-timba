#include <OCTOPython/OctoPython.h>
#include <MEQ/Axis.h>
    
namespace MeqUtils
{
using namespace OctoPython;

LocalDebugContext_ns;
inline std::string sdebug (int=0) { return "MeqUtils"; }

static int dum = aidRegistry_Meq();

static PyObject * get_axis_number (PyObject *, PyObject *args)
{
  PyObject * axis_id;
  // ref count of object is not increased, so do not attach ref
  if( !PyArg_ParseTuple(args,"O",&axis_id) )
    return NULL;
  try
  {
    // convert ID to string, then to HIID
    HIID id;
    if( PyString_Check(axis_id) )
      id = HIID(PyString_AsString(axis_id));
    else 
    {
      PyObjectRef objstr(PyObject_Str(axis_id));
      id = HIID(PyString_AsString(*objstr));
    }
    // look up in map
    int iaxis = Meq::Axis::axis(id);
    return PyInt_FromLong(iaxis);
  }
  catchStandardErrors(NULL);
  returnNone;
}

static PyObject * get_axis_id (PyObject *, PyObject *args)
{
  int axis_num;
  // ref count of object is not increased, so do not attach ref
  if( !PyArg_ParseTuple(args,"i",&axis_num) )
    return NULL;
  try
  {
    const HIID & id = Meq::Axis::axisId(axis_num);
    return PyString_FromString(id.toString().c_str());
  }
  catchStandardErrors(NULL);
  returnNone;
}

static PyObject * set_axis_list (PyObject *, PyObject *args)
{
  PyObject * axislist;
  // ref count of object is not increased, so do not attach ref
  if( !PyArg_ParseTuple(args,"O",&axislist) )
    return NULL;

  try
  {
    // make sure argument is a sequence
    if( !PySequence_Check(axislist) )
      returnError(NULL,Type,"sequence of axis ids expected");

    // convert to vector of HIIDs
    int naxis = PySequence_Length(axislist);
    if( naxis > Meq::Axis::MaxAxis )
      returnError(NULL,Value,"too many axis ids specified");

    std::vector<HIID> axis_map(naxis);

    for( int i=0; i<naxis; i++ )
    {
      PyObjectRef item = PySequence_GetItem(axislist,i);
      PyObjectRef itemstr = PyObject_Str(*item);
      // null HIIDs are represented as "(null)", which doesn't convert
      // to HIID. Just in case, catch all conversion errors and use a null id
      HIID id;
      try         { id = HIID(PyString_AsString(*itemstr)); }
      catch(...)  { id.clear(); }
      axis_map[i] = id;
    }
    // now set the axis map
    Meq::Axis::setAxisMap(axis_map);
  }
  catchStandardErrors(NULL);
  
  returnNone;
}

  
// -----------------------------------------------------------------------
// Module initialization
// -----------------------------------------------------------------------
static PyMethodDef MeqUtilMethods[] = {
    { "get_axis_number",get_axis_number,METH_VARARGS,
          "returns axis associated with given ID" },
    { "get_axis_id",get_axis_id,METH_VARARGS,
          "returns axis ID for given axis number" },
    { "set_axis_list",set_axis_list,METH_VARARGS,
          "changes the axis list" },
    { NULL, NULL, 0, NULL} };       /* Sentinel */

        
void initMeqUtilsModule ()
{
  Debug::Context::initialize();
  
  // init the module
  PyObject *module = Py_InitModule3("mequtils",MeqUtilMethods,
        "various utilities for python-side meqkernel support");
  if( !module )
    Throw("Py_InitModule3(\"mequtils\") failed");
  
  PyObjectRef timbamod = PyImport_ImportModule("Timba");  
  PyModule_AddObject(*timbamod,"mequtils",module);

  PyModule_AddObject(module,"max_axis",PyInt_FromLong(Meq::Axis::MaxAxis));
  
  // drop out on error
  if( PyErr_Occurred() )
    Throw("can't initialize module mequtils");
}
  

extern "C" 
{    
    
PyMODINIT_FUNC initmequtils ()
{
  Debug::Context::initialize();
  
  try
  {
    initMeqUtilsModule();
  }
  catch( std::exception &exc )
  {
    Py_FatalError(exc.what());
  }
}


} // extern "C"


} // namespace MeqUtils

InitDebugContext(MeqUtils,"MeqUtils");


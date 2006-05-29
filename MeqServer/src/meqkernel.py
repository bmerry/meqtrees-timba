#!/usr/bin/python
# standard python interface module for meqserver

import sys
import traceback

# sys.argv is not present when embedding a Python interpreter, but some
# packages (i.e. numarray) seem to fall over when it is not found. So we
# inject it
if not hasattr(sys,'argv'):
  setattr(sys,'argv',['meqkernel']);

# now import the rest
from Timba import dmi
from Timba import utils
import meqserver_interface
import sys
import imp
import os.path


_dbg = utils.verbosity(0,name='meqkernel');
_dprint = _dbg.dprint;
_dprintf = _dbg.dprintf;

_header_handlers = [];
_footer_handlers = [];

def reset ():
  global _header_handlers;
  global _footer_handlers;
  _header_handlers = [];
  _footer_handlers = [];
  
# helper function to set node state  
def set_state (node,**fields):
  """helper function to set the state of a node specified by name or
  nodeindex""";
  rec = dmi.record(state=dmi.record(fields));
  if isinstance(node,str):
    rec.name = node;
  elif isinstance(node,int):
    rec.nodeindex = node;
  else:
    raise TypeError,'illegal node argumnent';
  # pass command to kernel
  meqserver_interface.mqexec('Node.Set.State',rec,True); # True=silent
  
  
def process_vis_header (header):
  global _header_handlers;
  _dprint(0,"calling",len(_header_handlers),"header handlers");
  for handler in _header_handlers:
    handler(header);


def process_vis_footer (footer):
  """standard method called whenever a vis-footer is received.
  Comment out to disable.
  """
  global _footer_handlers;
  _dprint(0,"calling",len(_footer_handlers),"footer handlers");
  for handler in _footer_handlers:
    handler(footer);

# def process_vis_tile (tile):
#   """standard method called whenever a tile is received.
#   Comment out to disable. Since tiles currently have no Python representation,
#   this method is useless.
#   """
#   pass;

_initmod = None;

# sets the verbosity level
def set_verbose (level):
  _dbg.set_verbose(level);

def process_init (rec):
  # reset internals
  reset();
  # do we have an init-script in the header?
  _dprint(0,rec);
  try: script = rec.python_init;
  except AttributeError:
    _dprint(0,"no init-script specified, ignoring");
    return;
  try:
    # if a filename is supplied, try to import as file
    if script.endswith('.py'):
      # expand "~" and "$VAR" in filename
      script = filename = os.path.expandvars(os.path.expanduser(script));
      # now, if script is a relative pathname (doesn't start with '/'), try to find it in
      # various paths
      if not os.path.isabs(script):
        for dd in ["./"] + sys.path:
          filename = os.path.join(dd,script);
          if os.path.isfile(filename):
            break;
        else:
          raise ValueError,"script not found anywhere in path: "+script;
      _dprint(0,"importing init-script",filename);
      # open the script file
      infile = file(filename,'r');
      # now import the script as a module
      global _initmod;
      modname = '__initscript';
      try:
        imp.acquire_lock();
        _initmod = imp.load_module(modname,infile,filename,('.py','r',imp.PY_SOURCE));
      finally:
        imp.release_lock();
        infile.close();
    # else simply treat as module name
    else:
      _dprint(0,"importing init-module",script);
      _initmod = __import__(script);    
      # since __import__ returns the top-level package, use this
      # code from the Python docs to get to the ultimate module
      components = script.split('.')
      for comp in components[1:]:
          _initmod = getattr(_initmod, comp)
    # add standard names from script, if found
    global _header_handlers;
    global _footer_handlers;
    for nm,lst in (('process_vis_header',_header_handlers),('process_vis_footer',_footer_handlers)):
      handler = getattr(_initmod,nm,None);
      _dprint(0,'found handler',nm,'in script');
      if handler:
        lst.append(handler);
    return None;
  except: # catch-all for any errors during import
    (exctype,excvalue,tb) = sys.exc_info();
    _dprint(0,'exception',sys.exc_info(),'importing init-module',script);
    traceback.print_exc();
    raise;

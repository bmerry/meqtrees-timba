# JEN_matrix.py:

# Demonstrates the following MeqTree features:
# - Various matrix operations
# - Especially 2x2 matrices




 
#********************************************************************************
# Initialisation:
#********************************************************************************

from Timba.TDL import *
from Timba.Meq import meq

# from Timba.Contrib.JEN.util import JEN_bookmarks

Settings.forest_state.cache_policy = 100
Settings.forest_state.bookmarks = []



#********************************************************************************
# The function under the 'blue button':
#********************************************************************************

def _define_forest (ns, **kwargs):
   """Definition of a 'forest' of one or more trees"""


# Matrix ops:
#   1511 2006-09-14 14:36 Identity.cc
#   3039 2006-09-14 14:36 Transpose.cc
#  16019 2006-09-14 14:36 MatrixMultiply.cc
#   7603 2006-09-14 14:36 MatrixInvert22.cc
#   3139 2006-09-14 14:36 Stokes.cc            ??


   # Make two 'leaf' nodes that show some variation over freq/time. 
   a = ns['a'] << Meq.Time()
   b = ns['b'] << Meq.Freq()

   # The root node of the tree can have any name, but in this example it
   # should be named 'result', because this name is used in the default
   # execute command (see below), and the bookmark.
   result = ns['result'] << Meq.Add(a,b)

   # Make a bookmark of the result node, for easy viewing:
   bm = record(name='result', viewer='Result Plotter',
               udi='/node/result', publish=True)
   Settings.forest_state.bookmarks.append(bm)

   # Finished:
   return True



#********************************************************************************
# The function under the TDL Exec button:
#********************************************************************************

def _tdl_job_execute (mqs, parent):
    """Execute the forest, starting at the named node"""
    domain = meq.domain(1,10,1,10)                            # (f1,f2,t1,t2)
    cells = meq.cells(domain, num_freq=10, num_time=11)
    request = meq.request(cells, rqtype='ev')
    result = mqs.meq('Node.Execute',record(name='result', request=request))
    return result
       

#********************************************************************************
# Comments:
#********************************************************************************

#********************************************************************************
#********************************************************************************





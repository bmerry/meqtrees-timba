# MG_JEN_solver.py

# Short description:
#   Simple demonstration(s) of solver behaviour


# Author: Jan Noordam (JEN), Dwingeloo

# History:
# - 23 aug 2005: creation
# - 02 oct 2005: added demo for tiled solutions
# - 03 oct 2005: added epsilon (iteration control)

# Copyright: The MeqTree Foundation 



#********************************************************************************
#********************************************************************************
#**************** PART II: Preample and initialisation **************************
#********************************************************************************
#********************************************************************************

from Timba.TDL import *

from numarray import *

from Timba.Contrib.JEN import MG_JEN_exec
from Timba.Contrib.JEN import MG_JEN_forest_state
from Timba.Contrib.JEN import MG_JEN_funklet

#-------------------------------------------------------------------------
# Script control record (may be edited here):

MG = MG_JEN_exec.MG_init('MG_JEN_solver.py',
                         last_changed='h02oct2005',
                         nfreq=20,                  # nr of freq cells in request
                         ntime=20,                  # nr of time cells in request
                         trace=False)               # If True, produce progress messages  

MG.ab = record(parmtable=None,                      # name of AIPS++ MeqParm table
               use_previous=True,                   # if True, start with previous solution
               time_tile_size=4,                    # used in tiled solutions
               freq_tile_size=10,                 # used in tiled solutions
               dflt_a = array([[1,.3,.1],[.1,.2,.3]]),
               dflt_b = array([[-1,-.3,.1],[.1,.2,-.3]]),

               num_iter=10,                         # nr of solver iterations
               epsilon=1e-4,                        # controls automatic nr of iterations
               debug_level=20)                      # solver debug level


# Check the MG record, and replace any referenced values
MG = MG_JEN_exec.MG_check(MG)


#-------------------------------------------------------------------------
# The forest state record will be included automatically in the tree.
# Just assign fields to: Settings.forest_state[key] = ...

MG_JEN_forest_state.init(MG)






#********************************************************************************
#********************************************************************************
#**************** PART III: Required test/demo function *************************
#********************************************************************************
#********************************************************************************


def _define_forest (ns):
   """Definition of a MeqForest for demonstration/testing/experimentation
   of the subject of this MG script, and its importable functions"""

   # Perform some common functions, and return an empty list (cc=[]):
   cc = MG_JEN_exec.on_entry (ns, MG)

   #--------------------------------------------------------------------
   # Test ab: Make a solver with a single condeq, with children a and b:
   # First make the solvable parm (a):
   tiling = record()
   if MG.ab['time_tile_size']: tiling.time = MG.ab['time_tile_size']
   if MG.ab['freq_tile_size']: tiling.freq = MG.ab['freq_tile_size']
   a = ns.a << Meq.Parm(MG.ab['dflt_a'], node_groups='Parm',
                        use_previous=MG.ab['use_previous'],
                        tiling=tiling,
                        table_name=MG.ab['parmtable'])

   # The condeq takes the difference between the solvable parm (a) and
   # the 'constant' parm (b):
   b = ns.b << Meq.Parm(MG.ab['dflt_b'], node_groups='Parm')
   condeq = ns << Meq.Condeq(a,b)

   # The solver tries to minimise the condeq result (i.e. a-b): 
   solver = ns << Meq.Solver(condeq, solvable=[a],
                             num_iter=MG.ab['num_iter'],
                             epsilon=MG.ab['epsilon'],
                             debug_level=MG.ab['debug_level'])
   cc.append(solver)
   
   # Make a page of bookmarks for easy viewing:
   page_name = 'solver_ab'
   MG_JEN_forest_state.bookmark(a, page=page_name)
   MG_JEN_forest_state.bookmark(b, page=page_name)
   MG_JEN_forest_state.bookmark(solver, page=page_name)
   MG_JEN_forest_state.bookmark(condeq, page=page_name)
   MG_JEN_forest_state.bookmark(solver, page=page_name, viewer='ParmFiddler')
   
   # Finished: 
   return MG_JEN_exec.on_exit (ns, MG, cc)







#********************************************************************************
#********************************************************************************
#******************** PART IV: Optional: Importable functions *******************
#********************************************************************************
#********************************************************************************


# From: Michiel Brentjens <brentjens@astron.nl>
# To: "Oleg M. Smirnov" <smirnov@astron.nl>, Jan Noordam <noordam@astron.nl>, 
#     Maaijke Mevius <mevius@astron.nl>
# Subject: Update matrix343.py and Solver.{h,cc}
# Date: Fri, 30 Sep 2005 14:07:10 +0200

# Hi all,

# I've fixed a serious bug in my matrix343.py tree. From now on it fits both 
# source fluxes correctly. Furthermore I made the solver stop ignoring the 
# "epsilon" initrec field.
# (De initrec die je bij creatie aan de solver meegeeft. ik heb zelf echter de 
# gewoonte die settings aan de solver door te geven vlak VOOR ik mqs.init() 
# aanroep, zodat ik onafhankelijk van de _define_forest() routine de solver 
# settings in de _tdl_job_x() kan zetten.) 

# epsilon = (chisq(n)-chisq(n-1)) / (chisq(n)+chisq(n-1))

# - epsilon<0 means that chisq is getting smaller, so we are moving in
#   the right direction
# - abs(epsilon) will go to zero as we approach convergence

# >From now on the solver stops iterating when
#  * iteration == num_iter
#       OR
#  * abs(fit) < epsilon AND fit < 0.0

# 10^{-4} appears to be a sensible setting for epsilon.

# fit < 0.0 implies that chi-squared decreased during the last iteration. One 
# should NEVER stop after iterations that increased chi-squared. Set num_iter 
# to 20 or 40 or something similar to catch difficult cases.

# I added two fields to the solver metrics: 
#  * Iterations: number of iterations used in solution
#  * Converged: indicates whether convergence was achieved.


# Michiel






#********************************************************************************
#********************************************************************************
#*****************  PART V: Forest execution routines ***************************
#********************************************************************************
#********************************************************************************


def _test_forest (mqs, parent):
   return MG_JEN_exec.meqforest (mqs, parent,
                                 nfreq=MG['nfreq'], ntime=MG['ntime'],
                                 f1=0, f2=1, t1=0, t2=1) 


#********************************************************************************
#********************************************************************************
#******************** PART VI: Standalone test routines *************************
#********************************************************************************
#********************************************************************************


if __name__ == '__main__':
   print '\n*******************\n** Local test of:',MG.script_name,':\n'

   if 1:
      MG_JEN_exec.without_meqserver(MG.script_name, callback=_define_forest)

   # Various specific tests:
   ns = NodeScope()


   if 1:
       MG_JEN_exec.display_object (MG, 'MG', MG.script_name)
       # MG_JEN_exec.display_subtree (rr, MG.script_name, full=1)
   print '\n** End of local test of:',MG.script_name,'\n*******************\n'
       
#********************************************************************************
#********************************************************************************





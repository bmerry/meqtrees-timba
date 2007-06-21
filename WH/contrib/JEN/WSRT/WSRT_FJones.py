# file: ../WSRT/WSRT_FJones.py

# History:
# - 15jun2007: creation (from Grunting/WSRT_Joneset.py)

# Description:

# WSRT FJones matrix module, derived from Grunt.Joneset22, with TDLOptions

# Copyright: The MeqTree Foundation


#======================================================================================
# Preamble:
#======================================================================================

from Timba.TDL import *
from Timba.Meq import meq

from Timba.Contrib.JEN.Grunt import Joneset22


#=================================================================================================
# Functions to streamline the use of WSRT Jones matrices: 
#=================================================================================================

#--------------------------------------------------------------------------------------------

def FJones_parmgroups(full=False):
    """Return the available groups of MeqParms"""
    pg = ['FJones','Frm']
    return pg



class FJones (Joneset22.FJones):
    """Class that represents a set of 2x2 WSRT FJones matrices.
    For the moment, the ionospheric Faraday rotation is assumed
    to be the same for all stations, and the entire FOV."""

    def __init__(self, ns, name='FJones', quals=[],
                 override=None,
                 stations=None, simulate=False):
        
        # Just use the generic FJones in Grunt/Joneset22.py
        Joneset22.FJones.__init__(self, ns, quals=quals, name=name,
                                  telescope='WSRT',
                                  polrep='linear',
                                  override=override,
                                  stations=stations, simulate=simulate)
        return None


     
#===============================================================
# Test routine (with meqbrowser):
#===============================================================

def _define_forest(ns):

    cc = []
    simulate = True

    jones = FJones(ns, quals=[], simulate=simulate)
    cc.append(jones.visualize())
    jones.display(full=True)
        
    ns.result << Meq.Composer(children=cc)
    return True

#---------------------------------------------------------------

def _tdl_job_execute (mqs, parent):
    """Execute the forest, starting at the named node"""
    domain = meq.domain(1.0e8,1.1e8,1,1000)                            # (f1,f2,t1,t2)
    cells = meq.cells(domain, num_freq=1, num_time=100)
    request = meq.request(cells, rqtype='ev')
    result = mqs.meq('Node.Execute',record(name='result', request=request))
    return result
       


#===============================================================
# Test routine (standalone):
#===============================================================

if __name__ == '__main__':
    ns = NodeScope()


    if 1:
        J = FJones(ns, quals=['xxx'])
        J.display(full=True)


#===============================================================
    
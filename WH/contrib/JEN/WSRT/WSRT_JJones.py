# file: ../WSRT/WSRT_JJones.py

# History:
# - 15jun2007: creation (from Grunting/WSRT_Joneset.py)

# Description:

# WSRT JJones matrix module, derived from Grunt.Joneset22, with TDLOptions

# Copyright: The MeqTree Foundation


#======================================================================================
# Preamble:
#======================================================================================

#
#% $Id$ 
#
#
# Copyright (C) 2002-2007
# The MeqTree Foundation & 
# ASTRON (Netherlands Foundation for Research in Astronomy)
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>,
# or write to the Free Software Foundation, Inc., 
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from Timba.TDL import *
from Timba.Meq import meq

from Timba.Contrib.JEN.Grunt import Joneset22


#=================================================================================================
# Functions to streamline the use of WSRT Jones matrices: 
#=================================================================================================


def TDL_parmgroups(full=False):
    """Return the available groups of MeqParms"""
    pg = [None,'JJones','Jdiag','Joffdiag']
    return TDLCompileOption('TDL_JJones_solvable', 'groups of solvable JJones parms',pg,
                            doc='select group(s) of solvable parms ...')


#--------------------------------------------------------------------------------------------

TDLCompileOption('TDL_diagonal',"diagonal",[True,False],
                 doc='if diagonal, ...')

#--------------------------------------------------------------------------------------------


class JJones (Joneset22.JJones):
    """Class that represents a set of 2x2 WSRT JJones matrices.
    Each of the 4 complex elements of a station Jones matrix
    is assumed to be independent. The parameters are their real
    and imaginary parts (i.e. 8 real parameters per station)."""

    def __init__(self, ns, name='JJones', quals=[], 
                 diagonal=TDL_diagonal,
                 override=None,
                 stations=None, simulate=False):

        print '** diagonal=',diagonal

        # Just use the generic JJones in Grunt/Joneset22.py
        Joneset22.JJones.__init__(self, ns, quals=quals, name=name,
                                  polrep='linear',
                                  telescope='WSRT',
                                  diagonal=diagonal,
                                  override=override,
                                  stations=stations, simulate=simulate)
        return None


     
#===============================================================
# Test routine (with meqbrowser):
#===============================================================

def _define_forest(ns):

    cc = []
    simulate = True

    jones = JJones(ns, quals=[], simulate=simulate,
                        diagonal=TDL_diagonal)
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
        J = JJones(ns, quals=['xxx'], diagonal=TDL_diagonal)
        J.display(full=True)


#===============================================================
    

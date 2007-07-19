# file: ../Grunt/Condexet22.py

# History:
# - 18jan2007: creation
# - 23feb2007: second iteration
# - 02apr2007: adapted to QualScope etc

# Description:

# The Condexet22 class encapsulates a set of 2x2 condeq matrices.
# It is derived from the Matrixet22 class, and created with a Matrixet
# class (lhs), which provides the left-hand-side (lhs) children of the
# condeqs. Two functions create condeqs:
# - .make_condeqs(rhs) uses a right-hand-side (rhs) Matrixet22, which
#   provides the second children of the condeqs. It is assumed that the
#   rhs matrix indices occur in the lhs also.
# - .make_redun_condeqs(redun) equates the redundant lhs matrices with
#   each other. A 'redun' dict specifies which pairs of matrices have equal
#   ('redundant') baselines. 

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

from Timba.Contrib.JEN.Grunt import Matrixet22

from copy import deepcopy

# For testing only:
import Meow
# from Timba.Contrib.JEN.Grunt import Joneset22
from Timba.Contrib.JEN.Grunt import Visset22
from Timba.Contrib.JEN.Grunt import RedunVisset22


Settings.forest_state.cache_policy = 100

# Global counter used to generate unique node-names
# unique = -1

        
#======================================================================================

class Condexet22 (Matrixet22.Matrixet22):
    """Class that represents a set of 2x2 matrices of MeqCondeq nodes,
    which generate condition equations for a MeqSolver node. The left-hand
    side (lhs) is a Visset22 object with measured data, while the right-hand
    side (rhs) contains predicted visibilities."""

    def __init__(self, lhs, quals=[], label='cdxet',
                 wgt=None, select='*'):

        self._lhs = lhs
        self._wgt = wgt
        self._select = select

        # Placeholders:
        self._rhs = None
        self._redun = None

        self._condeq_name = 'condeq'

        # Initialise its Matrixet22 object:
        Matrixet22.Matrixet22.__init__(self, lhs.ns(), quals=quals, label=label)

        return None

    #-------------------------------------------------------------------

    def oneliner(self):
        """Return a one-line summary of this object"""
        ss = str(type(self))
        ss += '  '+str(self.label())
        ss += '  lhs='+str(self._lhs.label())
        if self._rhs: ss += '  rhs='+str(self._rhs.label())
        ss += '  quals='+str(self.ns()._qualstring())
        return ss


    def display_specific(self, full=False):
        """Print the specific part of the summary of this object"""
        print ' * lhs: '+str(self._lhs.oneliner())
        print ' * select: '+str(self._select)
        if self._rhs:
            print ' * rhs: '+str(self._rhs.oneliner())
        if self._redun:
            print ' * redun: '
            for key in self._redun.keys():
                print '  - '+str(key)+': '
        print ' * wgt: '+str(type(self._wgt))
        nodes = self.get_condeqs(matrel='*')
        print ' * list of condeq nodes ('+str(len(nodes))+'):'
        for k,node in enumerate(nodes):
            print '  - '+str(k)+': '+str(node) 
        return True

    #-----------------------------------------------------------------------------

    def get_condeqs (self, matrel='*'):
        """Get a list of the condeq nodes defined with make_condeqs() etc."""
        nodes = []
        if matrel=='*':
            for i in self.list_indices():
                nodes.append(self._matrixet(*i))
        else:
            nodes = self.extract_matrix_element(matrel)
        return nodes
        

    #--------------------------------------------------------------------------

    def make_condeqs (self, rhs=None, unop=None):
        """Make condeq matrices by equating the corresponding matrices 
        of the internal lhs, and the given rhs Matrixet22 objects.
        Optionally, apply an unary operation to both sides before equating."""

        self._rhs = rhs
        ns = self._ns._merge(self._rhs.ns())
        indices = []
        # Use the indices (order) of the rhs.....?
        ii = self._rhs.list_indices()                    # selection....?
        name = self._condeq_name
        qnode = ns[name]
        for i in ii:
            node1 = self._lhs._matrixet(*i)
            node2 = self._rhs._matrixet(*i)
            if node1.initialized() and node2.initialized():
                if unop:
                    # Optionally, apply a unary operation on both inputs:
                    node1 = ns.unop(unop)('lhs')(*i) << getattr(Meq, unop)(node1)
                    node2 = ns.unop(unop)('rhs')(*i) << getattr(Meq, unop)(node2)
                indices.append(i)
                qnode(*i) << Meq.Condeq(node1, node2)
        self._matrixet = qnode
        self.indices(new=indices)
        return True


    #------------------------------------------------------------------
    
    def make_redun_condeqs (self, redun, unop=None):
        """Make condeq matrices by equating pairs of matrices that represent
        equal (redundant) baselines in the internal lhs Matrixet22 object.
        The pairs of ifr-indices, and their identifying labels, are specified
        as lists (in fields named 'pairs' and 'labels') in the given dict redun. 
        Optionally, apply an unary operation to both sides before equating.
        NB: The redun condeqs are ADDED to condeqs that were already there.
            This allows the combining of selfcal and redun equations.
        NB: For an alternative approach, see RedunVisset22.py."""

        ns = self._ns._derive('redun')
        name = self._condeq_name
        qnode = ns[name]
        indices = self.indices()                 # NB: Allows ADDING of condeqs to earlier!!
        for k,pair in enumerate(redun['pairs']):
            node1 = self._lhs._matrixet(*pair[0])
            node2 = self._lhs._matrixet(*pair[1])
            if unop:
                # Optionally, apply a unary operation on both inputs:
                node1 = ns.unop(unop)('lhs')(k) << getattr(Meq, unop)(node1)
                node2 = ns.unop(unop)('rhs')(k) << getattr(Meq, unop)(node2)
            # The new matrixet index has 5 parts: 
            index = list(pair[0])                # the 2 stations of ifr1          
            index.extend(pair[1])                # the 2 stations of ifr2
            index.append(redun['labels'][k])     # the label (baseline length)
            indices.append(index)
            qnode(*index) << Meq.Condeq(node1, node2)
        self._matrixet = qnode
        self.indices(new=indices)
        return True





#======================================================================================
#======================================================================================
#======================================================================================
# Stand-alone helper routines:
#======================================================================================

def get_WSRT_1D_station_pos(sep9A=36):
    """Helper function to get 1D WSRT station positions (m), depending on
    separation 9-A (m). Used for redundant-spacing calibration.""" 
    xx = range(14)
    for i in range(10): xx[i] = i*144.0
    xx[10] = xx[9]+sep9A                     # A = 9 + sep9A
    xx[11] = xx[10]+72                       # B = A + 72
    xx[12] = xx[10]+(xx[9]-xx[0])            # C = A + (9-0)
    xx[13] = xx[12]+72                       # D = C + 72
    return xx

#-------------------------------------------------------------------------------------

def make_WSRT_redun_pairs (ifrs=None, sep9A=36, select='all'):
    """Create a list of redundant pairs of WSRT ifrs""" 
    rr = dict(pairs=[], labels=[])
    xx = get_WSRT_1D_station_pos(sep9A=sep9A)
    for i in range(len(ifrs)-1):
        ifr1 = ifrs[i]
        b1 = xx[ifr1[1]-1] - xx[ifr1[0]-1]            # ifr stations are 1-relative!
        for j in range(i+1,len(ifrs)):
            ifr2 = ifrs[j]
            b2 = xx[ifr2[1]-1] - xx[ifr2[0]-1]        # ifr stations are 1-relative!
            if b2==b1:
                rr['pairs'].append([ifr1,ifr2])
                rr['labels'].append(str(int(b1)))
                break
    return rr








#===============================================================
# Test routine (with meqbrowser):
#===============================================================

def _define_forest(ns):

    cc = []

    num_stations = 5
    ANTENNAS = range(1,num_stations+1)
    array = Meow.IfrArray(ns,ANTENNAS)
    # observation = Meow.Observation(ns)
    lhs = Visset22.Visset22(ns, label='lhs', array=array)
    lhs.fill_with_identical_matrices(stddev=0.01)
    cc.append(lhs.visualize())
    lhs.display()

    unop=None
    unop='Abs'
    matrel = '*'
    # matrel = 'm11'

    if True:
        pred = Visset22.Visset22(ns, label='pred', array=array)
        pred.fill_with_identical_matrices(stddev=0.1)
        pred.display()
        cc.append(pred.visualize())
        cdx = Condexet22(ns, lhs=lhs)
        cdx.make_condeqs(rhs=pred, unop=unop)
        condeqs = cdx.get_condeqs(matrel)
        cc.append(cdx.visualize())
        cdx.display()
        cc.append(cdx.bundle())

    ns.result << Meq.Composer(children=cc)
    return True

#---------------------------------------------------------------

def _tdl_job_execute (mqs, parent):
    """Execute the forest, starting at the named node"""
    domain = meq.domain(1.0e8,1.1e8,1,10)                            # (f1,f2,t1,t2)
    cells = meq.cells(domain, num_freq=10, num_time=11)
    request = meq.request(cells, rqtype='ev')
    result = mqs.meq('Node.Execute',record(name='result', request=request))
    return result
       



#=======================================================================
# Test program (standalone):
#=======================================================================

if __name__ == '__main__':
    ns = NodeScope()

    if 1:
        num_stations = 5
        ANTENNAS = range(1,num_stations+1)
        array = Meow.IfrArray(ns,ANTENNAS)
        # observation = Meow.Observation(ns)
        lhs = Visset22.Visset22(ns, label='lhs', array=array)
        lhs.fill_with_identical_matrices()
        lhs.display()
        cdx = Condexet22(lhs=lhs)
        cdx.display(recurse=2)

    if 0:
        pred = Visset22.Visset22(ns, label='pred', array=array)
        pred.fill_with_identical_matrices()
        pred.display()
        cdx.make_condeqs(rhs=pred, unop='Abs')
        cdx.visualize()
        cdx.display(recurse=3)

        if 0:
            redun = make_WSRT_redun_pairs (ifrs=array.ifrs(), sep9A=36, select='all')
            print 'redun=',redun
            cdx.make_redun_condeqs (redun, unop=None)
            cdx.display(recurse=3)

    if 0:
        redun = RedunVisset22.make_WSRT_redun_groups (ifrs=array.ifrs(), sep9A=36,
                                                      rhs='all4', select='all')
        rhs = RedunVisset22.RedunVisset22(ns, label='rhs', array=array,
                                          redun=redun, polar=False)
        # rhs.display()
        cdx.make_condeqs(rhs=rhs, unop=None)
        # cdx.visualize()
        cdx.display(recurse=3)
        cdx.show_matrix_subtree(recurse=2)

#=======================================================================
# Remarks:

#=======================================================================

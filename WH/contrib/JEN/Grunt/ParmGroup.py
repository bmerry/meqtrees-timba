# file: ../Grunt/ParmGroup.py

# History:
# - 25dec2006: creation
# - 03jan2007: re-implemented as a specialization of class NodeGroup
# - 03jan2007: created another specialization class SimulatedParmGroup 

# Description:

# The ParmGroup class encapsulates a named group of MeqParm nodes,
# or subtrees that generate simulated values for MeqParm nodes.
# ParmGroups are created in modules that implement bits of a
# Measurement Equation that contain parameters, e.g. instrumental
# Jones matrices, or LSM source models. They may be used for
# solving or visualization. They are also useful for generating
# user interfaces that offer a choice of solvers, etc.

#==========================================================================

from Timba.TDL import *
from Timba.Meq import meq

from Timba.Contrib.JEN.Grunt import NodeGroup 

from Timba.Contrib.JEN.util import JEN_bookmarks
from Timba.Contrib.JEN import MG_JEN_dataCollect

from copy import deepcopy
import random
import math



#==========================================================================

class ParmGroup (NodeGroup.NodeGroup):
    """Class that represents a group of (somehow related) MeqParm nodes"""

    def __init__(self, ns, label='<pg>',
                 nodelist=[],
                 quals=[], descr=None, tags=[], node_groups=[],
                 color='blue', style='circle', size=8, pen=2,
                 default=None, override=None, rider=None):

        NodeGroup.NodeGroup.__init__(self, ns=ns, label=label,
                                     quals=quals, descr=descr, tags=tags, 
                                     color=color, style=style, size=size, pen=pen,
                                     nodelist=nodelist,
                                     rider=rider)

        # Information needed to create MeqParm nodes (see create_entry())
        self._default = deepcopy(default)
        if not isinstance(self._default, dict): self._default = dict()
        self._default.setdefault('value',0.0)
        
        # The information may be overridden:
        self._override = dict()
        if isinstance(override, dict):
            if override.has_key(label):                     # relevant for this ParmGroup
                self._override = deepcopy(override[label])  # copy ony the relevant part
        
        self._node_groups = deepcopy(node_groups)
        if not isinstance(self._node_groups,(list,tuple)):
            self._node_groups = [self._node_groups]
        if not 'Parm' in self._node_groups:
            self._node_groups.append('Parm')

        return None
                
    #-------------------------------------------------------------------

    def display_specific(self, full=False):
        """Print the specific part of the summary of this object"""
        print ' * default ('+str(len(self._default))+'):'
        for key in self._default.keys():
            print '   - '+str(key)+' = '+str(self._default[key])
        print ' * override ('+str(len(self._override))+'):'
        for key in self._override.keys():
            print '   - '+str(key)+' = '+str(self._override[key])
        print '   - node_groups: '+str(self._node_groups)
        return True



    #======================================================================
    # Create a new ParmGroup entry (i.e. a MeqParm node)
    #======================================================================

    def create_entry (self, qual=None):
        """Create an entry, i.e. MeqParm node, or a simulation subtree,
        and append it to the nodelist"""

        # If in a qualifier (qual) is specified, append it to the temporary quals list: 
        quals = self._quals.get(append=qual)
            
        node = self._ns.parm(*quals) << Meq.Parm(self._default['value'],
                                                 node_groups=self._node_groups,
                                                 tags=self._tags)

        # Append the new node to the internal nodelist:
        self.append_entry(node)
        return node


    def from_TDL_NodeSet():

        #------------------------------------------------------------------------
        
        # NB: If use_previous==True, the MeqParm will use its current funklet (if any)
        #     as starting point for the next snippet solution, unless a suitable funklet
        #     was found in the MeqParm table. If False, it will use the default funklet first.

        # Future (MXM, 10 jan 2006):
        # - default is a scalar, default = 1.0
        #   - NB: If neither init_funklet nor shape (nor table), then the shape
        #         of the default (default_value, really) still determines the solution...
        # - new keywords:
        #   - [polctype_]shape = [1,1,...]    [ntime, nfreq, ..]
        #     - 1-based,
        #     - default=None
        #     - shape overrides the shape of the initialising funklet, e.g. from parmtable
        #   - init_funklet = None
        #     - used for non-polc funklets, e.g. = polclog(0)
        #     - and for initialisation of other coeff than c00, e.g. polc([[],[]]) 

        # If subtile_size is specified (i.e. nonzero and not None), assume an integer.
        # This specifies the size (nr of cells) of the solution-tile in the time-direction.
        # This means that separate solutions are made for these tiles, which tile the domain.
        # Tiled solutions are efficient, because they reduce the node overhead
        # For the moment, only time-tiling is enabled...

        tiling = record()
        if rider['subtile_size']:
            tiling.time = rider['subtile_size']

        # The default value:
        if default==None:
            default = rider['c00_default']

        # Use the shape (of coeff array, 1-relative) if specified.
        # Otherwise, use the [tdeg,fdeg] polc degree (0-relative)
        shape = rider['funklet_shape']                   #............??
        if shape==None:
            shape = [0,0]
            if not rider['tfdeg']==None:
                shape = deepcopy(rider['tfdeg'])         # just in case.....
            # print key,'** shape =',shape
            shape[0] += 1                                # make 1-relative              
            shape[1] += 1                                # make 1-relative

        # Make the new MeqParm node (if necessary):
        node = ns[key](**quals)
        if compounder_children:
            parm = ns[key](**quals)
            if not parm.initialized():                   # made only once
                parm << Meq.Parm(init_funklet=init_funklet,
                                 tiling=tiling,
                                 use_previous=rider['use_previous'],
                                 reset_funklet=rider['reset_funklet'],
                                 auto_save=rider['auto_save'],
                                 save_all=rider['save_all'],
                                 node_groups=self.node_groups(),
                                 table_name=self.parmtable())
                self.NodeSet.set_MeqNode(parm, group=parmgroup)

            # The Compounder has more qualifiers than the Parm.
            # E.g. EJones_X is per station, but the compounder and its
            # children (l,m) are for a specific source (q=3c84)
            group = parmgroup                            # e.g. 'EJones'
            if isinstance(qual2, dict):
                for qkey in qual2.keys():
                    s1 = str(qual2[qkey])
                    quals[qkey] = s1
                    group += '_'+s1                      # e.g. 'EJones_3c84'
            node = ns[key](**quals)
            if not node.initialized():                   # made only once
                cc = compounder_children
                if not isinstance(cc, (list, tuple)): cc = [cc]
                cc.append(parm)
                node << Meq.Compounder(children=cc, common_axes=common_axes)
                self.NodeSet.set_MeqNode(node, group=group)
                self.NodeSet.append_MeqNode_eval(parm.name, append=node)

        elif node.initialized():                           # node already exists
            # Don't do anything, but return the existing node.
            pass

        elif init_funklet:
            node << Meq.Parm(init_funklet=init_funklet,
                             ### shape=shape,             # DON'T
                             # perturbation=1e-7,       # scale*1e-7
                             tiling=tiling,
                             use_previous=rider['use_previous'],
                             reset_funklet=rider['reset_funklet'],
                             auto_save=rider['auto_save'],
                             save_all=rider['save_all'],
                             node_groups=self.node_groups(),
                             table_name=self.parmtable())
            self.NodeSet.set_MeqNode(node, group=parmgroup)
            
        else:
            node << Meq.Parm(funklet=default,
                             shape=shape,
                             tiling=tiling,
                             save_all=rider['save_all'],
                             auto_save=rider['auto_save'],
                             reset_funklet=rider['reset_funklet'],
                             use_previous=rider['use_previous'],
                             node_groups=self.node_groups(),
                             table_name=self.parmtable())
            self.NodeSet.set_MeqNode(node, group=parmgroup)

        # Return the rootnode (MeqParm of MeqCompounder):
        return node




    #======================================================================
    # Function to fill the object with test data:
    #======================================================================

    def test(self):
        """Helper function to put in some standard entries for testing"""
        self.create_entry()
        self.create_entry(5)
        self.create_entry(6)
        return True








#==========================================================================
#==========================================================================
#==========================================================================
#==========================================================================


class SimulatedParmGroup (NodeGroup.NodeGroup):
    """Class that represents a group of nodes (subtrees) that simulate
    a group of MeqParm nodes (often used in conjunction with class ParmGroup)"""

    def __init__(self, ns, label='<pg>',
                 nodelist=[],
                 quals=[], descr=None, tags=[], node_groups=[],
                 color='blue', style='circle', size=8, pen=2,
                 simul=None, default=None, override=None,
                 rider=None):

        NodeGroup.NodeGroup.__init__(self, ns=ns, label=label,
                                     quals=quals, descr=descr, tags=tags, 
                                     color=color, style=style, size=size, pen=pen,
                                     nodelist=nodelist,
                                     rider=rider)

        # Make sure that tags/quals of the created nodes reflect the fact
        # that this is a simulated parameter.
        self._tags.append('simul')            # ....??
        self._quals.append('simul')

        # The default value of the MeqParm that is being simulated:
        self._default = deepcopy(default)
        if not isinstance(self._default, dict): self._default = dict()
        self._default.setdefault('value',0.0)
        
        # Information to create a simulation subtree (see create_entry())
        pp = dict()                           # Simulation control info
        if isinstance (simul, dict):
            pp = deepcopy(simul)
        pp.setdefault('scale', None)
        pp.setdefault('stddev', 0.1)          # stddev of default value (relative!) 
        pp.setdefault('Tsec', 1000.0)         # Time variation (cos) period
        pp.setdefault('Tstddev', 0.1)         # stddev of Tsec (relative!)
        # Some checks:
        if pp['scale']==None:
            pp['scale'] = abs(self._default['value'])  #   use the (non-zero!) default value
            if pp['scale']==0.0: pp['scale'] = 1.0
        # Store:
        self._simul = pp 

        # The information may be overridden:
        self._override = dict()
        if isinstance(override, dict):
            if override.has_key(label):                     # relevant for this ParmGroup
                self._override = deepcopy(override[label])  # copy ony the relevant part
        
        return None
                
    #-------------------------------------------------------------------

    def display_specific(self, full=False):
        """Print the specific part of the summary of this object"""
        print ' * simul ('+str(len(self._simul))+'):'
        for key in self._simul.keys():
            print '   - '+key+' = '+str(self._simul[key])
        print ' * default ('+str(len(self._default))+'):'
        for key in self._default.keys():
            print '   - '+str(key)+' = '+str(self._default[key])
        print ' * override ('+str(len(self._override))+'):'
        for key in self._override.keys():
            print '   - '+str(key)+' = '+str(self._override[key])
        return True


    #-------------------------------------------------------------------

    def create_entry (self, qual=None):
        """Create an entry, i.e. a simulation subtree, that simulates
        a MeqParm node that varies with time and/or frequency, and append
        it to the nodelist"""

        # If in a qualifier (qual) is specified, append it to the temporary quals list: 
        quals = self._quals.get(append=qual)

        pp = self._simul                                 # Convenience
            
        # Expression used:
        #  default += ampl*cos(2pi*time/Tsec),
        #  where both ampl and Tsec may vary from node to node.

        ampl = 0.0
        if pp['stddev']:                                # default variation
            stddev = pp['stddev']*pp['scale']           # NB: pp['stddev is relative
            ampl = random.gauss(ampl, stddev)
        ampl = self._ns.ampl(*quals) << Meq.Constant(ampl)
        
        Tsec = pp['Tsec']                               # variation period (sec)
        if pp['Tstddev']:
            stddev = pp['Tstddev']*pp['Tsec']           # NB: pp['Tstddev is relative
            Tsec = random.gauss(pp['Tsec'], stddev) 
        Tsec = self._ns.Tsec(*quals) << Meq.Constant(Tsec)
        time = self._ns << Meq.Time()
        pi2 = 2*math.pi
        costime = self._ns << Meq.Cos(pi2*time/Tsec)
        variation = self._ns.variation(*quals) << Meq.Multiply(ampl,costime)

        # Finally, add the variation to the default value:
        default = self._ns.default(*quals) << Meq.Constant(self._default['value'])
        node = self._ns.parm(*quals) << Meq.Add(default, variation, tags=self._tags)

        # Append the new node to the internal nodelist:
        self.append_entry(node)
        return node



    #======================================================================

    def test(self):
        """Helper function to put in some standard entries for testing"""
        self.create_entry()
        self.create_entry(5)
        self.create_entry(6)
        return True







#===============================================================
# Test routine (with meqbrowser):
#===============================================================

def _define_forest(ns):

    cc = []

    pg1 = ParmGroup(ns, 'pg1', rider=dict(matrel='m21'))
    pg1.test()
    cc.append(pg1.visualize())
    nn1 = pg1.nodelist()
    print 'nn1 =',nn1

    pg2 = SimulatedParmGroup(ns, 'pg2')
    pg2.test()
    cc.append(pg2.visualize())
    nn2 = pg2.nodelist()
    print 'nn2 =',nn2

    condeqs = []
    for i in range(len(nn1)):
        print '- i =',i
        condeqs.append(ns.condeq(i) << Meq.Condeq(nn1[i],nn2[i]))
    solver = ns.solver << Meq.Solver(children=condeqs, solvable=nn1)
    JEN_bookmarks.create(solver, page='solver')
    cc.append(solver)
        



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
       


#===============================================================
# Test routine:
#===============================================================

if __name__ == '__main__':
    ns = NodeScope()

    if 1:
        pg1 = ParmGroup(ns, 'pg1', rider=dict(matrel='m21'))
        pg1.test()
        pg1.display()

        if 0:
            dcoll = pg1.visualize()
            pg1.display_subtree (dcoll, txt='dcoll')

    if 1:
        simul = dict(Tsec=500)
        default = dict(value=-1.0)
        pg2 = SimulatedParmGroup(ns, 'pg2', simul=simul, default=default)
        pg2.test()
        pg2.display()



#===============================================================
    

# TDL_Joneset.py
#
# Author: J.E.Noordam
#
# Short description:
#    A Joneset object encapsulates 2x2 instrumental jones matrices for a set of stations.
#
# History:
#    - 02 sep 2005: creation
#    - 10 sep 2005: more or less stable
#    - 23 sep 2005: MeqParm: use_previous==True, self.parmtable
#    - 30 nov 2005: added comment to MeqParm() tile_size
#    - 03 dec 2005: replaced MG_JEN_exec with TDL_display
#    - 07 dec 2005: introduced self.__constrain (needs more thought)
#    - 02 jan 2006: adopted TDL_Parmset.py
#
# Full description:
#



#=================================================================================
# Preamble:
#=================================================================================

from Timba.TDL import *
from copy import deepcopy

from Timba.Trees import TDL_common
from Timba.Trees import TDL_Parmset
from Timba.Trees import TDL_radio_conventions




#=================================================================================
# Class Joneset
#=================================================================================


class Joneset (TDL_common.Super):
    """A Joneset object encapsulates 2x2 instrumental jones matrices for a set of stations"""

    def __init__(self, **pp):

        # Input arguments:
        pp.setdefault('scope', '<jscope>')           # used in visualisation etc
        pp.setdefault('jchar', None)                 # single-character identifier (e.g. 'G') 
        pp.setdefault('polrep', 'linear')
        pp.setdefault('punit', 'uvp')                # name of predict-unit (source/patch)
        pp.setdefault('unsolvable', False)           # if True, do NOT store parmgroup/solvegroup info
        pp.setdefault('parmtable', None)             # name of MeqParm table (AIPS++)

        self.__scope = pp['scope']
        self.__punit = pp['punit']

        TDL_common.Super.__init__(self, type='Joneset', **pp)

        self.__jchar = pp['jchar']
        if not isinstance(self.__jchar, str): self.__jchar = self.label()[0]
        self.__jchar = self.__jchar[0]               # single character

        # Define its Parmset object
        self.Parmset = TDL_Parmset.Parmset(**pp)
        self.Parmset.quals(dict(q=self.__punit))

        self.clear()

        # Polarisation representation
        self.__polrep = pp['polrep']
        self.__pols = ['X', 'Y']
        if self.__polrep == 'circular':
            self.__pols = ['R', 'L']
        return None

    def clear(self):
        self.__jones = dict()
        self.__plot_color = TDL_radio_conventions.plot_color()
        self.__plot_style = TDL_radio_conventions.plot_style()
        self.__plot_size = TDL_radio_conventions.plot_size()

    def __getitem__(self, key):
        """Get s station (key) 2x2 Jones matrix (node)"""
        # This allows indexing by key and by index nr:
        if isinstance(key, int): key = self.__jones.keys()[key]
        return self.__jones[key]

    def __setitem__(self, key, value):
        """Set the station (key) 2x2 Jones matrix (node)"""
        self.__jones[key] = value
        return self.__jones[key]

    def parmgroup(self, key=None, ipol=None, color=None, style='circle', size=10, corrs=None):
        """Register a parameter (MeqParm) group (frontend for Parmset.parmgroup())"""
        if isinstance(ipol, int): key = key+'_'+self.pols(ipol)     # append (X,Y,R,L) if requirec

        if corrs=='*': corrs = self.corrs_all()
        if corrs=='paral': corrs = self.corrs_paral()
        if corrs=='paral1': corrs = self.corrs_paral1()
        if corrs=='paral2': corrs = self.corrs_paral2()
        if corrs=='cross': corrs = self.corrs_cross()
        # if self.corrs_all().__contains__(corrs): corrs = corrs      # single corr (e.g. 'RR')
        rider = dict(condeq_corrs=corrs)

        self.Parmset.parmgroup(key=key, color=color, style=style, size=size, rider=rider)

        s = 'Register parmgroup: '+key+': '+str(color)+' '+str(style)+' '+str(size)+' '+str(corrs)+' '
        self.history(s)
        return key                                                  # return the actual key name


    def append(self, key=None, node=None):
        """Append a named (key) 2x2 jones matrix node to the internal jones set"""
        key = str(key)          # potential __getitem__() problems if key is integer!! 
        self.__jones[key] = node
        return self.len()


    def scope(self, new=None):
        if isinstance(new, str): self.__scope = new
        return self.__scope
    def jchar(self): return self.__jchar
    def punit(self): return self.__punit
    def polrep(self): return self.__polrep
    def pols(self, ipol=None):
        if ipol==None: return self.__pols
        return self.__pols[ipol-1]

    def corrs_paral(self):
      return [self.pols(1)+self.pols(1), self.pols(2)+self.pols(2)]
    def corrs_paral1(self): return [self.pols(1)+self.pols(1)]
    def corrs_paral2(self): return [self.pols(2)+self.pols(2)]
    def corrs_cross(self):
      return [self.pols(1)+self.pols(2), self.pols(2)+self.pols(1)]
    def corrs_all(self):
      return [self.pols(1)+self.pols(1), self.pols(1)+self.pols(1),
              self.pols(2)+self.pols(2), self.pols(2)+self.pols(2)]

    def jones(self): return self.__jones
    def len(self): return len(self.__jones)
    def keys(self): return self.__jones.keys()
    def has_key(self, key): return self.keys().__contains__(key)

    def plot_color(self): return self.__plot_color
    def plot_style(self): return self.__plot_style
    def plot_size(self): return self.__plot_size
            
    def nodenames(self, select='*'):
        """Return the names of (a selection of) the jones matrix node names"""
        nn = []
        for key in self.keys():
            if isinstance(self.__jones[key], str):
                nn.append(self.__jones[key])
            else:
                nn.append(self.__jones[key].name)
        if len(nn)==0: return '<empty>'
        if select=='first': return nn[0]
        if select=='last': return nn[len(nn)-1]
        return nn

    def oneliner(self):
        """Make a one-line summary of this Joneset object"""
        s = TDL_common.Super.oneliner(self)
        s += ' ('+str(self.jchar())+')'
        s += ' punit='+str(self.punit())
        s += ' '+str(self.pols())
        s += ' len='+str(self.len())
        s += ' ('+str(self.nodenames('first'))+',...)'
        return s

    def display(self, txt=None, full=False):
        """Display a description of the contents of this Joneset object"""
        ss = TDL_common.Super.display (self, txt=txt, end=False)
        indent1 = 2*' '
        indent2 = 6*' '

        ss.append(indent1+' - '+str(self.Parmset.oneliner()))

        ss.append(indent1+' - Station jones matrix nodes ( '+str(self.len())+' ):')
        if full or self.len()<15:
            for key in self.keys():
                ss.append(indent2+' - '+key+' : '+str(self.__jones[key]))
        else:
            keys = self.keys()
            n = len(keys)-1
            ss.append(indent2+' - first: '+keys[0]+' : '+str(self.__jones[keys[0]]))
            ss.append(indent2+'   ....')
            ss.append(indent2+' - last:  '+keys[n]+' : '+str(self.__jones[keys[n]]))
        return TDL_common.Super.display_end (self, ss)


    def update(self, Joneset=None):
        """Update the internal info from another Joneset object:
        (used in Joneseq.make_Joneset())"""
        if Joneset==None: return False
        self.__jchar += Joneset.jchar()
        if self.Parmset.unsolvable():
            self.history(append='not updated from (unsolvable): '+Joneset.oneliner())
        elif not Joneset.Parmset.unsolvable():
            self.__plot_color.update(Joneset.plot_color())
            self.__plot_style.update(Joneset.plot_style())
            self.__plot_size.update(Joneset.plot_size())
            self.update_from_Parmset(Joneset.Parmset)
            self.history(append='updated from (not unsolvable): '+Joneset.oneliner())
        else:
            # A Joneset that is 'unsolvable' has no solvegroups.
            # However, its parmgroups might interfere with parmgroups
            # of the same name (e.g. Gphase) from solvable Jonesets.
            # Therefore, its parm info should NOT be copied here.
            self.history(append='not updated from (unsolvable): '+Joneset.oneliner())
        return True


    def update_from_Parmset(self, Parmset=None):
        """Update the internal info from a given Parmset"""
        if Parmset:
            self.Parmset.update(Parmset)
            self.history(append='updated from: '+Parmset.oneliner())
        self.__plot_color.update(self.Parmset.plot_color())
        self.__plot_style.update(self.Parmset.plot_style())
        self.__plot_size.update(self.Parmset.plot_size())
        return True









#=================================================================================
#=================================================================================
#=================================================================================
#=================================================================================

#=================================================================================
# Class Joneseq: Holds (and multiplies) a sequence of Joneset objects 
#=================================================================================


class Joneseq (TDL_common.Super):

    def __init__(self, **pp):
        pp.setdefault('label', 'JJones')
        TDL_common.Super.__init__(self, type='Joneseq', **pp)
        self.clear()
        return None

    def __getitem__(self, index):
        return self.__sequence[index]

    def clear(self):
        self.__scope = '<scope>'
        self.__sequence = []
        self.__polrep = '<polrep>'
        self.__punit = '<punit>'

    def sequence(self): return self.__sequence
    def keys(self): return self.__sequence.keys()
    def len(self): return len(self.__sequence)
    def empty(self): return (len(self.__sequence)==0)
    def polrep(self): return self.__polrep
    def scope(self): return self.__scope
    def punit(self): return self.__punit

    def oneliner(self):
        s = TDL_common.Super.oneliner(self)
        s = s+' punit='+str(self.punit())
        s = s+' polrep='+str(self.polrep())
        s = s+' len='+str(self.len())
        return s

    def display(self, txt=None, full=False):
        ss = TDL_common.Super.display (self, txt=txt, end=False)
        indent1 = 2*' '
        indent2 = 6*' '
        ss.append(indent1+' - Available Joneset sequence (.len() -> '+str(self.len())+' ):')
        for i in range(self.len()):
            ss.append(indent2+' - '+str(i)+' : '+self.__sequence[i].oneliner())
        return TDL_common.Super.display_end (self, ss)

    def append(self, Joneset=None):
        # Append a Joneset object to the internal sequence, after some checks:
        funcname = '.append():'
        jtype = Joneset.type()
        if not jtype=='Joneset':
            self.history(error=funcname+'not a Joneset, but'+jtype)
            return False

        # The Jonesets in the sequence should be consistent with each other: 
        if self.empty():
            # Collect information from the first one:
            self.__punit = Joneset.punit()
            self.__polrep = Joneset.polrep()
            self.__scope = Joneset.scope()
        else:
            # Compare with the info from the first one:
            if not Joneset.punit()==self.punit():
                self.history(error=funcname+'conflicting punit')
                return False
            if not Joneset.polrep()==self.polrep():
                self.history(error=funcname+'conflicting polrep')
                return False
            if not Joneset.scope()==self.scope():
                self.history(error=funcname+'conflicting scope')
                return False

        # OK, append to the internal sequence:
        self.__sequence.append(Joneset)
        self.history(str(self.len())+': '+funcname+Joneset.label())
        return self.len()


    def make_Joneset(self, ns):
        # Obtain a combined Joneset from the internal Joneset sequence:
        funcname = '.make_Joneset():'

        # Some checks:
        if not self.ok():
            self.history(error=funcname+'problems (not ok())')
            return False
        elif self.empty():
            self.history(error=funcname+'empty sequence')
            return False
        elif self.len()==1:
            # The internal sequence has only one member:
            self.__sequence[0].history('Extracted single item from: '+self.oneliner())
            return self.__sequence[0]              # just return the single one

        # The internal sequence has multiple Jonesets:
        # For each station (key), make a list cc[key] of input jones matrix nodes:
        keys = self.__sequence[0].keys()           # the stations (keys) of the first Joneset
        cc = dict() ;
        kwquals = dict()
        quals = dict()
        for key in keys:
            cc[key] = []
            kwquals[key] = dict()
            quals[key] = []
        punits = []
        labels = []
        for js in self.__sequence:                 # for all Jonesets in the sequence
            js_jones = js.jones()                  # get its set of jones matrices
            for key in keys:
                kwquals[key].update(js_jones[key].kwquals)
                quals[key].extend(list(js_jones[key].quals))
                cc[key].append(js_jones[key])
            punits.append(js.punit())              # should all be the same...!!            
            labels.append(js.label())           
            
        # Make new 2x2 jones matrices by matrix multiplication: 
        # Create a new Joneset
        newJoneset = Joneset(label=self.label(), punit=self.punit(),
                             polrep=self.polrep(), scope=self.scope())
        newJoneset.history('Matrix multiplication of: '+self.oneliner())
        for key in keys:
            newJoneset[key] = ns.JJones(**kwquals[key])(*quals[key]) << Meq.MatrixMultiply(children=cc[key])
        newJoneset.history('input sequence: '+str(labels))
        newJoneset.history('input punits (should be the same!): '+str(punits))

        # Update the parmgroup info from Joneset to Joneset:
        for js in self.sequence():
            newJoneset.update(js)

        return newJoneset




#========================================================================
# Helper routines:
#========================================================================

# Counter service (use to automatically generate unique node names)

_counters = {}

def _counter (key, increment=0, reset=False, trace=True):
    global _counters
    _counters.setdefault(key, 0)
    if reset: _counters[key] = 0
    _counters[key] += increment
    if trace: print '** TDL_Joneset: _counters(',key,') =',_counters[key]
    return _counters[key]






#========================================================================
# Test routine:
#========================================================================

if __name__ == '__main__':
    print '\n*******************\n** Local test of: TDL_Joneset.py:\n'
    from numarray import *
    from Timba.Trees import TDL_display
    # from Timba.Trees import JEN_record
    ns = NodeScope()
    nsim = ns.Subscope('_')
    
    # stations = range(3)
    js = Joneset(label='initial', polrep='circular')
    js.display('initial')

    if 0:
        print '** dir(js) ->',dir(js)
        print '** js.__doc__ ->',js.__doc__
        print '** js.__str__() ->',js.__str__()
        print '** js.__module__ ->',js.__module__
        print

    if 0:
        js.parmtable('xxx')

    if 0:
        js = Joneset(label='GJones', polrep='circular')
        p1 = js.parmgroup('Gphase', ipol=1, color='red', corrs=js.corrs_paral1())
        a2 = js.parmgroup('Gampl', ipol=2, color='blue', corrs=js.corrs_paral2())
        a1 = js.parmgroup('Gampl', ipol=1, color='blue', corrs=js.corrs_paral1())
        d12 = js.parmgroup('Ddang', color='blue', corrs=js.corrs_cross())
        d2 = js.parmgroup('Ddang', ipol=2, color='blue', corrs=js.corrs_cross())
        js.node_groups(['G','QQ'])
        js.node_groups(['G'])

        for station in range(14):
          js.MeqParm(reset=True)
          js.define_MeqParm(ns, p1, station=station, default=0)
          js.define_MeqParm(ns, a2, station=station, default=1)
          js.define_MeqParm(ns, a1, station=station, default=1)
          js.define_MeqParm(ns, d2, station=station, default=0)
          js.define_MeqParm(ns, d12, station=station, default=0)
          ss = js.MeqParm(update=True)
          js.append(station, '<jones_matrix for station '+str(station)+'>')

        js.define_solvegroup('p1_a2', [p1, a2])
        js.define_solvegroup('a1_a2', [a1, a2])
        js.define_solvegroup('ALL', js.parmgroup().keys())

    if 0:
        # Access to jones etc
        print
        print 'js.jones()[key]:'
        for key in js.keys(): print '-',key, js.jones()[key]
        print 'js[key]:'
        for key in js.keys(): print '-',key, js[key]
        print 'item in js:'
        for item in js: print '- item:',item
        print

    if 0:
        jones0 = ns << Meq.Constant(array([[11,12],[21,22]]), dim=[2,2])
        TDL_display.subtree(jones0, 'jones0', full=True)
        print '\n** jones0=',jones0
        print type(jones0),isinstance(jones0,type(ns<<0))
        js.nominal(ns, jones0)                   # <--- no longer exists....
        js.display('.nominal()')
        print '** .nodenames() -> (',len(js.nodenames()),'):',js.nodenames()
    
    if 0:
        Gjones = MG_JEN_Joneset.GJones (ns, stations=stations)
        Bjones = MG_JEN_Joneset.BJones (ns, stations=stations)

    if 0:
        # Joneseq object:
        jseq = Joneseq(label='initial')
        jseq.display('empty')
        jseq.append(js)
        jseq.append(js)
        jseq.append(js)
        jseq.display('filled')

    if 0:
        print js.parmtable('cal_BJones')
        print js.check_parmtable_extension()

    if 1:
        # Display the final result:
        k = 0 ; TDL_display.subtree(js[k], 'js['+str(k)+']', full=True, recurse=3)
        js.display('final result')

    print '\n*******************\n** End of local test of: TDL_Joneset.py:\n'




#============================================================================================









 


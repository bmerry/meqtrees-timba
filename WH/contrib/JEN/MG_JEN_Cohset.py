script_name = 'MG_JEN_Cohset.py'
last_changed = 'h10sep2005'

# Short description:
#   Functions dealing with sets (all ifrs) of 2x2 cohaerency matrices 

# Keywords: ....

# Author: Jan Noordam (JEN), Dwingeloo

# History:
# - 24 aug 2005: creation
# - 05 sep 2005: adapted to Cohset/Joneset objects

# Copyright: The MeqTree Foundation 

#================================================================================
# Import of Python modules:

from Timba.TDL import *
from Timba.Meq import meq

from numarray import *
# from string import *
# from copy import deepcopy

from Timba.Trees import TDL_Cohset
from Timba.Trees import TDL_Joneset
# from Timba.Trees import TDL_Sixpack
from Timba.Contrib.JEN import MG_JEN_Joneset
from Timba.Contrib.JEN import MG_JEN_Sixpack

from Timba.Contrib.JEN import MG_JEN_exec
from Timba.Contrib.JEN import MG_JEN_forest_state
from Timba.Contrib.JEN import MG_JEN_twig
from Timba.Contrib.JEN import MG_JEN_dataCollect
from Timba.Contrib.JEN import MG_JEN_flagger

#-------------------------------------------------------------------------
# The forest state record will be included automatically in the tree.
# Just assign fields to: Settings.forest_state[key] = ...

MG_JEN_forest_state.init(script_name)


#================================================================================
# Tree definition routine (may be executed from the browser):
# To be used as example, for experimentation, and automatic testing.
#================================================================================

def _define_forest (ns): 
   cc = MG_JEN_exec.on_entry (ns, script_name)

   # Make the Cohset ifrs (and the Joneset stations):
   ifrs = TDL_Cohset.stations2ifrs(range(0,5))
   stations = TDL_Cohset.ifrs2stations(ifrs)

   # Source/patch to be used for simulation/selfcal:
   punit = 'unpol'
   # punit = 'unpol2'
   # punit = '3c147'
   # punit = 'RMtest'
   # punit = 'QUV'
   # punit = 'QU'
   # punit =  'SItest'

   # Make a Cohset for the specified ifrs, with simulated uv-data: 
   jones = ['G']
   # jones = ['D']
   # jones = ['G','D']
   jones  = ['B']  
   Cohset = simulate(ns, ifrs, punit=punit, jones=jones)
   visualise (ns, Cohset)
   visualise (ns, Cohset, type='spectra')

   if False:
       # Check by correcting with the corrupting JJones:
       global simulated_JJones                               # see .simulate()
       Cohset.correct(ns, simulated_JJones)
       visualise (ns, Cohset)
       visualise (ns, Cohset, type='spectra')

   if False:
       insert_flagger (ns, Cohset, scope='residual', unop=['Real','Imag'], visu=True)
       visualise (ns, Cohset)
       visualise (ns, Cohset, type='spectra')

   if True:
       # Insert a solver for a named group of MeqParms (e.g. 'GJones'):
       jones = ['G']
       # punit = 'QUV'
       punit = 'unpol10'
       Joneset = JJones(ns, stations, punit=punit, jones=jones)
       predicted = predict (ns, punit=punit, ifrs=ifrs, Joneset=Joneset)
       sgname = 'GJones'
       # sgname = 'DJones'
       # sgname = ['DJones', 'GJones']
       insert_solver (ns, solvegroup=sgname, measured=Cohset, predicted=predicted, 
                                correct=Joneset, num_iter=10)
       visualise (ns, Cohset)
       visualise (ns, Cohset, type='spectra')
 
   if False:
       # Insert another solver for a different group of MeqParms (e.g. 'DJones'):
       # NB: Concatenating solvers this way causes problems...
       DJoneset = JJones(ns, stations, punit=punit, jones=['D'])
       Dpredicted = predict (ns, punit=punit, ifrs=ifrs, Joneset=DJoneset)
       insert_solver (ns, solvegroup='DJones', measured=Cohset, predicted=Dpredicted, 
                               correct = DJoneset, num_iter=10)
       visualise (ns, Cohset) 
       visualise (ns, Cohset, type='spectra')


   # Tie the trees for the different ifrs together in an artificial 'sink':
   cc.append(Cohset.simul_sink(ns))

   # Finished: 
   return MG_JEN_exec.on_exit (ns, script_name, cc)






#================================================================================
# Optional: Importable function(s): To be imported into user scripts.
#================================================================================


#--------------------------------------------------------------------------------
# Produce a Cohset for the specified ifrs, with simulated uv-data: 

def simulate(ns, ifrs, **pp):
   funcname = 'MG_JEN_Cohset.simulate(): '

   pp.setdefault('jones', [])
   pp.setdefault('punit', 'unpol')

   pp.setdefault('stddev_Gampl', 0.1) 
   pp.setdefault('stddev_Gphase', 0.1) 
   pp.setdefault('fdeg_Gampl', 1) 
   pp.setdefault('fdeg_Gphase', 1) 
   pp.setdefault('tdeg_Gampl', 0) 
   pp.setdefault('tdeg_Gphase', 0) 

   pp.setdefault('stddev_Breal', 0.1) 
   pp.setdefault('stddev_Bimag', 0.1) 
   pp.setdefault('fdeg_Breal', 3) 
   pp.setdefault('fdeg_Bimag', 3) 
   pp.setdefault('tdeg_Breal', 0) 
   pp.setdefault('tdeg_Bimag', 0) 

   pp.setdefault('stddev_dang', 0.01) 
   pp.setdefault('stddev_dell', 0.01) 
   pp.setdefault('fdeg_dang', 1) 
   pp.setdefault('fdeg_dell', 1) 
   pp.setdefault('tdeg_dang', 0) 
   pp.setdefault('tdeg_dell', 0) 

   pp.setdefault('RM', 0.1) 
   pp.setdefault('PZD', 0.2)
   pp.setdefault('stddev_noise', 0.0)
   pp = record(pp)

   # Recommended ways to mark nodes that contains simulated data: 
   scope = 'simulated'           # mark the Cohset/Jonesets (visualisation)
   nsim = ns.Subscope('_')       # prepend all simulation nodes with _:: 

   # Optional: corrupt the uvdata with simulated jones matrices: 
   if not isinstance(pp.jones, (list,tuple)): pp.jones = [pp.jones]
   if len(pp.jones)>0:
       stations = TDL_Cohset.ifrs2stations(ifrs) 
       jseq = TDL_Joneset.Joneseq()
       for jones in pp.jones:
           if jones=='G':
               jseq.append(MG_JEN_Joneset.GJones (nsim, scope=scope, stations=stations, punit=pp.punit, 
                                                  solvable=False,
                                                  fdeg_Gampl=pp.fdeg_Gampl, fdeg_Gphase=pp.fdeg_Gphase,
                                                  tdeg_Gampl=pp.tdeg_Gampl, tdeg_Gphase=pp.tdeg_Gphase,
                                                  stddev_Gampl=pp.stddev_Gampl, stddev_Gphase=pp.stddev_Gphase))
           elif jones=='B':
               jseq.append(MG_JEN_Joneset.BJones (nsim, scope=scope, stations=stations, punit=pp.punit, 
                                                  solvable=False,
                                                  fdeg_Breal=pp.fdeg_Breal, fdeg_Bimag=pp.fdeg_Bimag,
                                                  tdeg_Breal=pp.tdeg_Breal, tdeg_Bimag=pp.tdeg_Bimag,
                                                  stddev_Breal=pp.stddev_Breal, stddev_Bimag=pp.stddev_Bimag))
           elif jones=='F':
               jseq.append(MG_JEN_Joneset.FJones (nsim, scope=scope, stations=stations, punit=pp.punit, 
                                                  solvable=False, RM=pp.RM))
           elif jones=='D':
               jseq.append(MG_JEN_Joneset.DJones_WSRT (nsim, scope=scope, stations=stations, punit=pp.punit, 
                                                       solvable=False, PZD=pp.PZD,
                                                       fdeg_dang=pp.fdeg_dang, fdeg_dell=pp.fdeg_dell,
                                                       tdeg_dang=pp.tdeg_dang, tdeg_dell=pp.tdeg_dell,
                                                       stddev_dang=pp.stddev_dang, stddev_dell=pp.stddev_dang))
           else:
               print '** jones not recognised:',jones,'from:',pp.jones
               
       # Matrix-multiply the collected jones matrices in jseq to a 2x2 Joneset:
       global simulated_JJones
       simulated_JJones = jseq.make_Joneset(nsim)
       MG_JEN_forest_state.object(jseq, funcname)
       MG_JEN_forest_state.object(simulated_JJones, funcname)

   # Make the Cohset with simulated/corrupted uvdata:
   Cohset = predict (nsim, scope=scope, punit=pp.punit, ifrs=ifrs, Joneset=simulated_JJones)

   # Add some gaussian noise to the data
   # (NB: More advanced noise may be added to the Cohset after this function)
   if (pp.stddev_noise>0): addnoise (ns, Cohset, stddev=pp.stddev_noise)

   MG_JEN_forest_state.object(Cohset, funcname)
   return Cohset

#--------------------------------------------------------------------------------------
# Make a JJones Joneset from the specified sequence (list) of jones matrices:

def JJones(ns, stations, **pp):
    funcname = 'MG_JEN_Cohset.JJones(): '

    pp.setdefault('jones', []) 
    pp.setdefault('scope', 'predicted') 
    pp.setdefault('punit', 'uvp')

    pp.setdefault('fdeg_Gampl', 1) 
    pp.setdefault('fdeg_Gphase', 1) 
    pp.setdefault('tdeg_Gampl', 0) 
    pp.setdefault('tdeg_Gphase', 0) 
    
    pp.setdefault('fdeg_Breal', 3) 
    pp.setdefault('fdeg_Bimag', 3) 
    pp.setdefault('tdeg_Breal', 0) 
    pp.setdefault('tdeg_Bimag', 0) 
    
    pp.setdefault('fdeg_dang', 1) 
    pp.setdefault('fdeg_dell', 1) 
    pp.setdefault('tdeg_dang', 0) 
    pp.setdefault('tdeg_dell', 0) 

    pp.setdefault('RM', 0.1) 
    pp.setdefault('PZD', 0.1)
    pp = record(pp)

    jseq = TDL_Joneset.Joneseq()
    if not isinstance(pp.jones, (list,tuple)): pp.jones = [pp.jones]
    for jones in pp.jones:
        if jones=='G':
            jseq.append(MG_JEN_Joneset.GJones (ns, scope=pp.scope, punit=pp.punit, stations=stations,
                                               fdeg_Gampl=pp.fdeg_Gampl, fdeg_Gphase=pp.fdeg_Gphase,
                                               tdeg_Gampl=pp.tdeg_Gampl, tdeg_Gphase=pp.tdeg_Gphase,
                                               Gscale=0))
        elif jones=='B':
            jseq.append(MG_JEN_Joneset.BJones (ns, scope=pp.scope, punit=pp.punit, stations=stations,
                                               fdeg_Breal=pp.fdeg_Breal, fdeg_Bimag=pp.fdeg_Bimag,
                                               tdeg_Breal=pp.tdeg_Breal, tdeg_Bimag=pp.tdeg_Bimag,
                                               Bscale=0))
        elif jones=='F':
            jseq.append(MG_JEN_Joneset.FJones (ns, scope=pp.scope, punit=pp.punit, stations=stations,
                                               Fscale=0, RM=pp.RM))
        elif jones=='D':
            jseq.append(MG_JEN_Joneset.DJones_WSRT (ns, scope=pp.scope, punit=pp.punit, stations=stations,
                                                    fdeg_dang=pp.fdeg_dang, fdeg_dell=pp.fdeg_dell,
                                                    tdeg_dang=pp.tdeg_dang, tdeg_dell=pp.tdeg_dell,
                                                    Dscale=0, PZD=pp.PZD))
        else:
            print '** jones not recognised:',jones,'from:',pp.jones
               
    # Matrix-multiply the collected jones matrices in jseq to a 2x2 Joneset:
    MG_JEN_forest_state.object(jseq, funcname)
    Joneset = jseq.make_Joneset(ns)
    MG_JEN_forest_state.object(Joneset, funcname)
    return Joneset
    
#======================================================================================
# Convert an (LSM) Sixpack into visibilities for linearly polarised receptors:
  
def Sixpack2linear (ns, Sixpack, name='nominal'):
    # Make a 2x2 coherency matrix (coh0) by multiplication with the Stokes matrix:
    funcname = 'MG_JEN_Cohset.Sixpack2linear(): '
    punit = Sixpack.label()
    name = name+'_XYYX'
    coh0 = ns[name](q=punit) << Meq.Matrix22(
        (ns['XX'](q=punit) << Sixpack.stokesI() + Sixpack.stokesQ()),
        (ns['XY'](q=punit) << Meq.ToComplex( Sixpack.stokesU(), Sixpack.stokesV())),
        (ns['YX'](q=punit) << Meq.Conj( ns['XY'](q=punit) )),
        (ns['YY'](q=punit) << Sixpack.stokesI() - Sixpack.stokesQ())
        ) * 0.5
    return coh0

#--------------------------------------------------------------------------------------
# Convert an (LSM) Sixpack into visibilities for circularly polarised receptors:

def Sixpack2circular (ns, Sixpack, name='nominal'):
    # Make a 2x2 coherency matrix (coh0) by multiplication with the Stokes matrix:
    funcname = 'MG_JEN_Cohset.Sixpack2circular(): '
    punit = Sixpack.label()
    name = name+'_RLLR'
    coh0 = ns[name](q=punit) << Meq.Matrix22(
        (ns['RR'](q=punit) << Sixpack.stokesI() + Sixpack.stokesV()),
        (ns['RL'](q=punit) << Meq.ToComplex( Sixpack.stokesQ(), Sixpack.stokesU())),
        (ns['LR'](q=punit) << Meq.Conj( ns['RL'](q=punit) )),
        (ns['LL'](q=punit) << Sixpack.stokesI() - Sixpack.stokesV())
        ) * 0.5
    return coh0



#======================================================================================

def addnoise (ns, Cohset, **pp):
    """add gaussian noise to the coherency matrices in Cohset""" 

    funcname = 'MG_JEN_Cohset.addnoise(): '

    # Input arguments:
    pp.setdefault('stddev', 1.0)          #
    pp.setdefault('unop', 'Exp')          #
    pp = record(pp)

    for key in Cohset.keys():
        s12 = Cohset.stations()[key]
        nsub = ns.Subscope('addnoise', s1=s12[0], s2=s12[1])
        noise = MG_JEN_twig.gaussnoise (nsub, dims=Cohset.dims(),
                                        stddev=pp.stddev, unop=pp.unop)
        coh = ns.noisy(s1=s12[0], s2=s12[1]) << Meq.Add(Cohset[key], noise)
        Cohset[key] = coh

    # Finished:
    s = funcname
    s = s+', stddev='+str(pp.stddev)
    s = s+', unop='+str(pp.unop)
    Cohset.history(s)
    MG_JEN_forest_state.history (funcname)
    return True









#======================================================================================

def predict (ns=0, Joneset=None, **pp):
    funcname = 'MG_JEN_Cohset.predict(): '

    # Input arguments:
    pp.setdefault('scope', 'rawdata')
    pp.setdefault('ifrs', [(0,1)])
    pp.setdefault('punit', 'unpol')
    pp.setdefault('polrep', 'linear')
    pp = record(pp)

    # Get the 6 punit subtrees:
    Sixpack = MG_JEN_Sixpack.newstar_source (ns, name=pp['punit'])

    # Make a 2x2 coherency matrix (coh0) by multiplication with the Stokes matrix:
    if pp['polrep']=='circular':
       coh0 = Sixpack2circular (ns, Sixpack, name='nominal')
    else:
       coh0 = Sixpack2linear (ns, Sixpack, name='nominal')

    # Create a Cohset object for the 2x2 cohaerencies of the given ifrs:
    Cohset = TDL_Cohset.Cohset(label='predict', origin=funcname, **pp)

    # Put the same node (coh0) with 'nominal' (i.e. uncorrupted) visibilities
    # into all ifr-slots of the Cohset:
    Cohset.nominal(ns, coh0)

    # Optionally, corrupt the Cohset visibilities with the instrumental effects
    # in the given Joneset of 2x2 station jones matrices:
    if not Joneset==None:
       Cohset.corrupt (ns, Joneset=Joneset)
       Cohset.display('.predict(): after corruption')

    # Finished:
    MG_JEN_forest_state.object(Sixpack, funcname)
    Cohset.history(funcname+' using '+Sixpack.oneliner())
    Cohset.history(funcname+' -> '+Cohset.oneliner())
    MG_JEN_forest_state.history (funcname)
    MG_JEN_forest_state.object(Cohset, funcname)
    return Cohset






#======================================================================================
# Insert a flagger:
#======================================================================================

def insert_flagger (ns, Cohset, **pp):
    """insert a flagger for the coherency matrices in Cohset""" 

    funcname = 'MG_JEN_Cohset.insert_flagger(): '

    # Input arguments:
    pp.setdefault('sigma', 5.0)              # flagged if exceeds sigma*stddev
    pp.setdefault('unop', 'Abs')             # unop used to make real data
    pp.setdefault('oper', 'GT')              # decision function (GT=Greater Than)
    pp.setdefault('flag_bit', 1)             # affected flag-bit
    pp.setdefault('merge', True)             # if True, merge the flags of 4 corrs
    pp.setdefault('visu', False)             # if True, visualise the result
    pp.setdefault('compare', False)          # ....
    pp = record(pp)

    # Insert flaggers for all ifrs:
    flagger_scope = 'flag_'+Cohset.scope()
    for key in Cohset.keys():
        s12 = Cohset.stations()[key]
        nsub = ns.Subscope(flagger_scope, s1=s12[0], s2=s12[1])
        coh = MG_JEN_flagger.flagger (nsub, Cohset[key],
                                      sigma=pp.sigma, unop=pp.unop, oper=pp.oper,
                                      flag_bit=pp.flag_bit, merge=pp.merge)
        Cohset[key] = coh

    # Visualise the result, if required:
    if pp.visu:
        visu_scope = 'flagged_'+Cohset.scope()
        visualise (ns, Cohset, scope=visu_scope, type='spectra')

    Cohset.scope('flagged')
    Cohset.history(funcname+' -> '+Cohset.oneliner())
    MG_JEN_forest_state.history (funcname)
    MG_JEN_forest_state.object(Cohset, funcname)
    return True



#======================================================================================
# Insert a solver for the specified solvegroup(s):
#======================================================================================

# - The 'measured' Cohset is assumed to be the main data stream.
# - The 'predicted' Cohset contains corrupted model visibilities.
# - The (optional) 'correct' Joneset contains the instrumental model
#   that is affected by this solver. If suppliedt, the measured data
#   will be corrected with the estimated values BEFORE the reqseq graft.
# - The (optional) 'compare' Joneset contains the simulated instrumental
#   values. If supplied they will be subtracted from the estimated values
#   when visualised. 


def insert_solver (ns, measured, predicted, correct=None, compare=None, **pp):
    """insert a named solver""" 

    funcname = 'MG_JEN_Cohset.solver(): '

    # Input arguments:
    pp.setdefault('solvegroup', [])        # list of solvegroup(s) to be solved for
    pp.setdefault('num_iter', 20)          # number of iterations
    pp.setdefault('debug_level', 10)       # solver debug_level
    pp.setdefault('visu', True)            # if True, include visualisation
    pp.setdefault('graft', True)           # if True, graft the solver on the Cohset stream
    pp = record(pp)

    # The solver name must correspond to one or more of the
    # predefined solvegroups of parms in the input Cohset(s).
    # These are collected from the Jonesets upstream.
    # The solver_name is just a concatenation of such solvegroup names:
    if isinstance(pp.solvegroup, str): pp.solvegroup = [pp.solvegroup]
    solver_name = pp.solvegroup[0]
    for i in range(len(pp.solvegroup)):
        if i>0: solver_name = solver_name+pp.solvegroup[i]

    # Use copies of the input Cohsets (corr selection etc): 
    Pohset = predicted.copy(label='predicted('+str(pp.solvegroup)+')')
    Pohset.label('solver_'+solver_name)
    Mohset = measured.copy(label='measured('+str(pp.solvegroup)+')')
    Mohset.label('solver_'+solver_name)

    # From here on, only the Pohset copy will be modified,
    # until it contains the MeqCondeq nodes for the solver.
    # It will be attached to the state_forest, for later inspection.
    Pohset.history(funcname+' input: '+str(pp))
    Pohset.history(funcname+' measured: '+measured.oneliner())
    Pohset.history(funcname+' predicted: '+predicted.oneliner())

    # Merge the parm/solver info from BOTH input Pohsets:
    # (the measured side may also have solvable parameters)
    # NB: This causes the parms from 'predicted' to be overridden by those from 'measured'....... 
    # Pohset.update_from_Cohset(measured)

    # Collect a list of names of solvable MeParms for the solver:
    corrs = []
    solvable = []
    for sgname in pp.solvegroup:
        if not Pohset.solvegroup().has_key(sgname):
            print '\n** solvegroup name not recognised:',sgname
            print '     choose from:',Pohset.solvegroup().keys()
            print
            return
        solvegroup = Pohset.solvegroup()[sgname]
        corrs.extend(Pohset.condeq_corrs()[sgname])
        for key in solvegroup:
            solvable.extend(Pohset.parmgroup()[key])

    # Make new Cohset objects with the relevant corrs only:
    Pohset.selcorr(ns, corrs)
    Mohset.selcorr(ns, corrs)
  
    # Make condeq nodes (use Pohset from here onwards):
    cc = []
    punit = predicted.punit()
    for key in Pohset.keys():
        if not measured.has_key(key):
            print '\n** key not recognised in measured Cohset:',key
            return
        s12 = Pohset.stations()[key]
        condeq = ns.condeq(solver_name)(s1=s12[0],s2=s12[1],q=punit) << Meq.Condeq(Mohset[key], Pohset[key])
        Pohset[key] = condeq
        cc.append(condeq)
    Pohset.display('after defining condeqs')

    # Visualise the condeqs, if required:
    dconc_condeq = dict()
    if pp.visu:
       Pohset.scope('condeq_'+solver_name)
       dconc_condeq = visualise (ns, Pohset, errorbars=True, graft=False)
       # NB: What about visualising MeqParms (solvegroups)?
       #     Possibly compared with their simulated values...
  
    # Make the solver node:
    solver = ns.solver(solver_name, q=punit) << Meq.Solver(children=cc,
                                                     solvable=solvable,
                                                     num_iter=pp.num_iter,
                                                     debug_level=pp.debug_level)

    # Make a bookmark for the solver plot:
    MG_JEN_forest_state.bookmark (solver, name=('solver: '+solver_name),
                                  udi='cache/result', viewer='Result Plotter',
                                  page=0, save=1, clear=0)

    # Add to the Pohset history:
    Pohset.history(funcname+' -> '+Pohset.oneliner())
    MG_JEN_forest_state.history (funcname)
    MG_JEN_forest_state.object(Pohset, funcname)

    # Optional: Correct the measured data with the given Joneset (correct).
    # This is the Joneset that has been affected by the solver.
    # NB: This correction should be inserted BEFORE the solver reqseq (see below),
    #         because otherwise it messes up the correction of the insertion ifr
    #         (one of the input Jones matrices is called before the solver....)
    if not correct==None:
	measured.correct(ns, correct)          # assume that correct is a Joneset


    # Tie the solver and its associated dcoll(s) with a MeqReqseq node.
    # If pp.graft==True such a reqseq node is inserted in each ifr data-stream
    keys = measured.keys()                     # main data stream
    solver_name = 'solver_'+solver_name        # used in reqseq name
    for key in keys:
       cc = [solver]                           # start a list of reqseq children (solver is first)
       for dkey in dconc_condeq.keys(): cc.append(dconc_condeq[dkey]['dcoll']) 
       result_index = 0 
       if pp.graft: 
          cc.append(measured[key])             # measured Cohset (main data-stream) should be LAST!
          result_index = len(cc)-1             # the reqseq should return the result of the main data stream
       reqseq = ns.reqseq.qmerge(measured[key])(solver_name, q=punit) << Meq.ReqSeq(children=cc, result_index=result_index)
 
       # Optional, insert (graft) a solver reqseq on the main data stream (measured):
       if pp.graft: measured[key] = reqseq     # the original measured[key] is a child of reqseq

    # Return the last reqseq node, which may be used to pass requests to.
    # However, this is not necessary if pp.graft==True, so this reqseq may be ignored. 
    return reqseq





#======================================================================================

def visualise(ns, Cohset, **pp):
    """visualises the 2x2 coherency matrices in Cohset"""

    funcname = 'MG_JEN_Cohset.visualise(): '
    uniqual = MG_JEN_forest_state.uniqual('MG_JEN_Cohset::visualise()')

    # Input arguments:
    pp.setdefault('type', 'realvsimag')     # plot type (realvsimag or spectra)
    pp.setdefault('errorbars', False)       # if True, plot stddev as crosses around mean
    pp.setdefault('graft', True)            # if True, graft the visu-nodes on the Cohset
    pp = record(pp)

    # Use a sub-scope where node-names are prepended with name
    # and may have other qualifiers: nsub = ns.subscope(name, '[qual_list]')
    visu_scope = 'visu_'+Cohset.scope()

    # The dataCollect nodes are visible, and should show the punit:
    dcoll_scope = Cohset.scope()+'_'+Cohset.punit()
  
    # Make separate lists of nodes per corr:
    corrs = Cohset.corrs()
    nodes = {}
    for corr in corrs:
        nodes[corr] = []

    for key in Cohset.keys():
        s12 = Cohset.stations()[key]
        coh = Cohset[key]
        for icorr in range(len(corrs)):
            corr = corrs[icorr]
            nsub = ns.Subscope(visu_scope+'_'+corr, s1=s12[0], s2=s12[1])
            selected = nsub.selector(icorr)(uniqual) << Meq.Selector (coh, index=icorr)
            nodes[corr].append(selected)

    # Make dcolls per corr, and collect groups of corrs:
    dcoll = dict()
    for corr in corrs:
        dc = MG_JEN_dataCollect.dcoll (ns, nodes[corr], 
	                               scope=dcoll_scope, tag=corr,
                                       type=pp.type, errorbars=pp.errorbars,
                                       color=Cohset.plot_color()[corr],
                                       style=Cohset.plot_style()[corr])
        if pp.type=='spectra':
           dcoll[corr] = dc
        elif pp.type=='realvsimag':
           key = 'allcorrs'
           dcoll.setdefault(key,[])
           dcoll[key].append(dc)
           if corr in ['XY','YX','RL','LR']:
              key = 'crosscorr'
              dcoll.setdefault(key,[])
              dcoll[key].append(dc)
           if True and corr in ['XX','YY','RR','LL']:
              key = 'paralcorr'
              dcoll.setdefault(key,[])
              dcoll[key].append(dc)

    # Make the final dcolls:
    dconc = dict()
    sc = []
    for key in dcoll.keys():
       bookpage = None
       if pp.type=='spectra':
          # Since spectra plots are crowded, make separate plots for the 4 corrs.
          # key = corr
          dc = dcoll[key]
          bookpage = dcoll_scope+'_spectra'
       elif pp.type=='realvsimag':
          # For realvsimag plots it is better to plot multiple corrs in the same plot.
          # key = allcorrs, [paralcorr], [crosscorr]
          # bookpage = dcoll_scope
          dc = MG_JEN_dataCollect.dconc(ns, dcoll[key], 
                                        scope=dcoll_scope,
                                        tag=key, bookpage=key)
       dconc[key] = dc                               # atach to output record
       sc.append (dc['dcoll'])                       # step-child for graft below
       if isinstance(bookpage, str):
          MG_JEN_forest_state.bookmark (dc['dcoll'], page=bookpage)
      

    MG_JEN_forest_state.history (funcname)
  
    if pp.graft:
        # Make the dcoll nodes step-children of a MeqSelector
        # node that is inserted before one of the coherency nodes:
        Cohset.graft(ns, sc, stepchild=True)
        return True

    else:
        # Return a dict of named dconc nodes that need requests:
        # Do NOT modify the input Cohset
        Cohset.history(funcname+' -> '+'dconc '+str(len(dconc)))
        return dconc



#==========================================================================
# Some convenience functions:
#==========================================================================

#--------------------------------------------------------------------------
# Display the subtree of the first ifr in the Cohset

def display_first_subtree (Cohset=0, recurse=3):
    key = Cohset.keys()[0]
    txt = 'coh[0/'+str(Cohset.len())+']'
    txt = txt+': key='+str(key)
    MG_JEN_exec.display_subtree(Cohset[key], txt, full=1, recurse=recurse)
    return














#********************************************************************************
# Initialisation and testing routines
# NB: this section should always be at the end of the script
#********************************************************************************


#-------------------------------------------------------------------------
# Meqforest execution routine (may be called from the browser):
# The 'mqs' argument is a meqserver proxy object.
# If not explicitly supplied, a default request will be used.

def _test_forest (mqs, parent):
   return MG_JEN_exec.meqforest (mqs, parent)


# Execute the forest for a sequence of requests:

def _tdl_job_sequence(mqs, parent):
    for x in range(10):
        MG_JEN_exec.meqforest (mqs, parent, nfreq=20, ntime=19,
                               f1=x, f2=x+1, t1=x, t2=x+1,
                               save=False, trace=False, wait=False)
    MG_JEN_exec.save_meqforest(mqs) 
    return True



#-------------------------------------------------------------------------
# Test routine to check the tree for consistency in the absence of a server

if __name__ == '__main__':
    print '\n*******************\n** Local test of:',script_name,':\n'

    # This is the default:
    if 0:
        MG_JEN_exec.without_meqserver(script_name, callback=_define_forest, recurse=3)

    # This is the place for some specific tests during development.
    ns = NodeScope()
    nsim = ns.Subscope('_')
    stations = range(0,3)
    ifrs  = [ (s1,s2) for s1 in stations for s2 in stations if s1<s2 ];
    cs = TDL_Cohset.Cohset(label='test', scops=script_name, ifrs=ifrs)

    if 0:   
        cs.display('initial')
       
    if 0:
        cs.spigots (ns)
           
    if 0:
        # coh = predict ()
        punit = 'unpol'
        # punit = '3c147'
        # punit = 'RMtest'
        jseq = TDL_Joneset.Joneseq()
        jseq.append(MG_JEN_Joneset.GJones (ns, stations=stations))
        js = jseq.make_Joneset(ns)
        cs = predict (ns, punit=punit, ifrs=ifrs, Joneset=js)
        visualise (ns, cs)
        addnoise (ns, cs)
        insert_flagger (ns, cs, scope='residual', unop=['Real','Imag'], visu=True)

    if 0:
        punit = 'unpol'
        # punit = '3c147'
        # punit = 'RMtest'
        Joneset = MG_JEN_Joneset.GJones (nsim, stations=stations, solvable=1)
        measured = predict (nsim, punit=punit, ifrs=ifrs, Joneset=Joneset)
        # measured.select(ns, corrs=['XX','YY'])
        
        Joneset = MG_JEN_Joneset.DJones_WSRT (ns, stations=stations)
        predicted = predict (ns, punit=punit, ifrs=ifrs, Joneset=Joneset)
        cs = predicted
        
        sgname = 'DJones'
        # sgname = ['DJones', 'GJones']
        cs = insert_solver (ns, solvegroup=sgname, measured=measured, predicted=predicted) 
           
    if 0:
        punit = 'unpol'
        Sixpack = MG_JEN_Sixpack.newstar_source (ns, name=punit)
        coh0 = Sixpack2circular (ns, Sixpack)
        MG_JEN_exec.display_subtree (coh0, 'coh0', full=1)
        coh0 = Sixpack2linear (ns, Sixpack)
        MG_JEN_exec.display_subtree (coh0, 'coh0', full=1)

    if 0:
        display_first_subtree(cs)
        cs.display('final result')

    # ............
    # MG_JEN_exec.display_subtree (rr, 'rr', full=1)
    print '\n** End of local test of:',script_name,'\n*******************\n'

#********************************************************************************
#********************************************************************************





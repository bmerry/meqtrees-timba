from Timba.TDL import *
from Timba.Meq import meq
from numarray import *
import os

from Timba.Contrib.OMS.IfrArray import IfrArray
from Timba.Contrib.OMS.Observation import Observation
from Timba.Contrib.OMS.SkyComponent import *
import clar_model

# MS name
TDLRuntimeOption('msname',"MS",["TEST_CLAR_27-480.MS","TEST_CLAR_27-4800.MS"],inline=True);


tile_size = 480
resample = None;
# resample = [480,1];
num_stations = 27

# CLAR beam width
# base HPBW is 5.3 arcmin at 800 MHz
beam_width = 5.3
ref_frequency = float(800*1e+6)

# MEP table for derived quantities fitted in this script
mep_derived = 'CLAR_DQ_27-480.mep';

# bookmark
Settings.forest_state = record(bookmarks=[
  record(name='Derived quantities',page=[
    record(viewer="Result Plotter",udi="/node/exp_v_gain:S2:1",pos=(0,0)),
    record(viewer="Result Plotter",udi="/node/EXP_V_GAIN:S2:1",pos=(0,1)),
    record(viewer="Result Plotter",udi="/node/ce_vgain:S2:1",pos=(0,2)),
    record(viewer="Result Plotter",udi="/node/exp_v_gain:S2:%d"%num_stations,pos=(1,0)),
    record(viewer="Result Plotter",udi="/node/EXP_V_GAIN:S2:%d"%num_stations,pos=(1,1)),
    record(viewer="Result Plotter",udi="/node/ce_vgain:S2:%d"%num_stations,pos=(1,2)),
    record(viewer="Result Plotter",udi="/node/uvw:%d"%(num_stations/2),pos=(2,0)),
    record(viewer="Result Plotter",udi="/node/uvw1:%d"%(num_stations/2),pos=(2,1)),
    record(viewer="Result Plotter",udi="/node/ce_uvw:%d"%(num_stations/2),pos=(2,2)),
    record(viewer="Result Plotter",udi="/node/solver_uvw:10",pos=(3,0)),
    record(viewer="Result Plotter",udi="/node/solver_vgain:1",pos=(3,1)),
    record(viewer="Result Plotter",udi="/node/solver_vgain:%d"%num_stations,pos=(3,2)),
#    record(viewer="Result Plotter",udi="/node/predict:1:6",pos=(3,1)),
#    record(viewer="Result Plotter",udi="/node/predict:1:14",pos=(3,2)),
#   record(viewer="Result Plotter",udi="/node/stokes:Q:3C343",pos=(1,0)),
#    record(viewer="Result Plotter",udi="/node/stokes:Q:3C343_1",pos=(1,1)),
#   record(viewer="Result Plotter",udi="/node/solver",pos=(1,1)),
  ]) \
]);

def tpolc (tdeg,c00=0.0):
  return Meq.Parm(create_polc(degree_f=0,degree_t=tdeg,c00=c00),
                  node_groups='Parm',
                  table_name=mep_derived);
  

def create_solver_defaults(num_iter=30,epsilon=1e-4,convergence_quota=0.9,solvable=[]):
    solver_defaults=record()
    solver_defaults.num_iter      = num_iter
    solver_defaults.epsilon       = epsilon
    solver_defaults.epsilon_deriv = epsilon
    solver_defaults.balanced_equations = False
    solver_defaults.convergence_quota = convergence_quota
    solver_defaults.save_funklets= True
    solver_defaults.last_update  = True
#See example in TDL/MeqClasses.py
    solver_defaults.solvable     = solvable
    return solver_defaults
    

def _define_forest(ns):
  # create array model
  stations = range(1,num_stations+1);
  array = IfrArray(ns,stations);
  obs = Observation(ns);
  
  # get list of all known directions
  dirs = clar_model.init_directions(ns);
                     
  # create nodes for simulating the CLAR beam
  ns.freq << Meq.Freq;
  # this is the half-power beam width at reference frequency
  ns.hpbw0 << Meq.Constant(beam_width);
  # this is the HPBW at the given frequency
  ns.hpbw << ns.hpbw0 * ref_frequency / ns.freq 
  # take inverse and square
  arcmin_radian = ns.arcmin_radian << 3437.75
  ns.ihpbw = arcmin_radian / ns.hpbw 
  ns.ihpbw_sq << Meq.Sqr(ns.ihpbw)

  # create nodes used to calculate AzEl of field centre as seen
  # from a specific station
  xyz = array.xyz();
  ln16 = ns.ln16 << -2.7725887;
    
  # we first build up the mathematical expression of a CLAR voltage
  # pattern for a source using the equations
  # log16 =  (-1.0) * log(16.0)
  # L,M give direction cosines of the source wrt field centre in
  # AzEl coordinate frame
  # L_gain = (L * L) / (widthl_ * widthl_)
  # sin_factor = sqr(sin(field centre elevation))
  # M_gain = (sin_factor * M * M ) / (widthm_ * widthm_)
  # voltage_gain = sqrt(exp(log16 * (L_gain + M_gain)))

  for st in array.stations():
    # first create AzEl node for field_centre as seen from this station
    azel0 = ns.azel0(st) << Meq.AzEl(radec=obs.radec0(),xyz=xyz(st))
    # get squared sine of elevation of field centre - used later to determine 
    # CLAR beam broadening
    sin_el_sq = ns.sin_el_sq(st) << Meq.Sqr(Meq.Sin(ns.el0(st) << Meq.Selector(azel0,index=1)));
    
    for name,dd in dirs.iteritems():
      # create AzEl node for source as seen from this station
      azel = ns.azel(name,st) << Meq.AzEl(radec=dd.radec(),xyz=xyz(st));

      # do computation of LMN of source wrt field centre in AzEl frame
      lmn_azel = ns.lmn_azel(name,st) << Meq.LMN(radec_0=azel0,radec=azel);
      l_azel = ns.l_azel(name,st) << Meq.Selector(lmn_azel,index=0);
      m_azel = ns.m_azel(name,st) << Meq.Selector(lmn_azel,index=1);

      # compute CLAR voltage gain as seen for this source at this station
      # first square L and M
      l_sq = ns.l_sq(name,st) << Meq.Sqr(l_azel);
      m_sq = ns.m_sq(name,st) << Meq.Sqr(m_azel);

      # add L and M gains together, then multiply by log 16
      vgain = ns.v_gain(name,st) << ( l_sq + m_sq*sin_el_sq )*ln16;

      # this now needs to be multiplied by width and exponent taken to get the
      # true beam power
      ns.exp_v_gain(name,st) << Meq.Exp(vgain*ns.ihpbw_sq);

  # now create solvers for everything
  solver_list = []
  radec0 = obs.radec0();
  # Measurements
  for sta in array.stations():
    # create solver + condeq for station UVWs
    uvw = array.uvw(radec0);     # computed UVWs 
    fitted_uvws = [ ns.u(sta).qadd(radec0) << tpolc(5),
                    ns.v(sta).qadd(radec0) << tpolc(5),
                    ns.w(sta).qadd(radec0) << tpolc(5)  ];
    ns.ce_uvw(sta) << Meq.Condeq(
      uvw(sta),
      ns.uvw1(sta) << Meq.Composer(*fitted_uvws)
    );
    defs = create_solver_defaults(solvable=[node.name for node in fitted_uvws]);
    solver_list.append(ns.solver_uvw(sta) << Meq.Solver(
        ns.ce_uvw(sta),mt_polling=False,mt_solve=False,**defs));
    # create solver for station beams patterns
    for name,dd in dirs.iteritems():
      # condeq for source-station E-term
      vgain = ns.V_GAIN(name,sta) << tpolc(6);
      ce = ns.ce_vgain(name,sta) << Meq.Condeq(
          ns.exp_v_gain(name,sta),
          ns.EXP_V_GAIN(name,sta) << Meq.Exp(vgain*ns.ihpbw_sq)
      );
    defs = create_solver_defaults(solvable=[ns.V_GAIN(name,sta).name for name in dirs.keys()]);
    solver_list.append(ns.solver_vgain(sta) << Meq.Solver(mt_polling=False,mt_solve=False,
        *[ns.ce_vgain(name,sta) for name in dirs.keys()],**defs));
        
  # create ReqMux for all solvers
  ns.solvers << Meq.ReqMux(mt_polling=True,*solver_list);

  global _vdm;
  if resample:
    ns.modres << Meq.ModRes(ns.solvers,num_cells=resample);
    _vdm = ns.VisDataMux << Meq.VisDataMux(pre=ns.modres);
  else:
    _vdm = ns.VisDataMux << Meq.VisDataMux(pre=ns.solvers);


def create_inputrec(msname, tile_size=1500,short=False):
    boioname = "boio."+msname+"."+str(tile_size);
    # if boio dump for this tiling exists, use it to save time
    # but watch out if you change the visibility data set!
    if False: # not short and os.access(boioname,os.R_OK):
      rec = record(boio=record(boio_file_name=boioname,boio_file_mode="r"));
    # else use MS, but tell the event channel to record itself to boio file
    else:
      rec = record();
      rec.ms_name          = msname
      rec.data_column_name = 'DATA'
      rec.tile_size        = tile_size
#      rec.selection = record(channel_start_index=0,
#                             channel_end_index=0,
#                             channel_increment=1,
#                             selection_string='')
#      if short:
#        rec.selection.selection_string = '';
#      else:
#        rec.record_input = boioname;
      rec = record(ms=rec);
    rec.python_init='Timba.Contrib.OMS.ReadVisHeader';
    return rec;



def _tdl_job_fit_derived_quantities (mqs,parent,write=True):
    inputrec        = create_inputrec(msname, tile_size=tile_size)
    
    req = meq.request();
    req.input  = inputrec;
    mqs.clearcache('VisDataMux');
    print 'VisDataMux request is ', req
    mqs.execute('VisDataMux',req,wait=(parent is None));
    pass



Settings.forest_state.cache_policy = 1  # 1 for smart caching, 100 for full caching
Settings.orphans_are_roots = True

if __name__ == '__main__':


    Timba.TDL._dbg.set_verbose(5);
    ns = NodeScope();
    _define_forest(ns);


    ns.Resolve();
    pass
              

from Timba.TDL import *
from Direction import *


class Observation (object):
  """An observation object represents observation-related properties.
  These are polarization type (circular or linear), plus the phase center
  direction. An observation also has an optional set of qualifiers 
  which are applied to all nodes created via this object (i.e. the ra/dec
  nodes of the phase center).
  """;
  def __init__(self,ns,circular=False,linear=False,
               quals=[],kwquals={}):
    self.ns = ns;
    if circular and linear:
      raise ValueError,"either circular=True or linerar=True must be specified, not both";
    self._circular = circular;
    self._quals = quals;
    self._kwquals = kwquals;
    self.phase_centre = \
        Direction(ns,None,0,0,constant=True,quals=quals,kwquals=kwquals);
    
  def circular (self):
    return self._circular;
    
  def radec0 (self):
    """returns radec node for the phase center direction""";
    return self.phase_centre.radec();
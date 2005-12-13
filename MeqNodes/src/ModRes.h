//# ModRes.h: modifies request resolutions
//#
//# Copyright (C) 2003
//# ASTRON (Netherlands Foundation for Research in Astronomy)
//# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
//#
//# This program is free software; you can redistribute it and/or modify
//# it under the terms of the GNU General Public License as published by
//# the Free Software Foundation; either version 2 of the License, or
//# (at your option) any later version.
//#
//# This program is distributed in the hope that it will be useful,
//# but WITHOUT ANY WARRANTY; without even the implied warranty of
//# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//# GNU General Public License for more details.
//#
//# You should have received a copy of the GNU General Public License
//# along with this program; if not, write to the Free Software
//# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//#
//# $Id$

#ifndef MEQNODES_MODRES_H
#define MEQNODES_MODRES_H
    
#include <MEQ/Node.h>
#include <MEQ/Cells.h>
#include <MEQ/AID-Meq.h>

#include <MeqNodes/TID-MeqNodes.h>
#pragma aidgroup MeqNodes
#pragma types #Meq::ModRes 
#pragma aid Factor Num Cells Resulution Index

// The comments below are used to automatically generate a default
// init-record for the class 

//defrec begin MeqModRes
//  Changes the resolution of a parent's Request before passing it on to the
//  child. Returns child result as is. Expects exactly one child.
//field: num_cells []
//  If specified, changes the number of cells along each axis. 
//  Must be a vector of 2 values (frequency axis, time axis), or a single 
//  value (for both axes). A value of 0 leaves the resolution along that axis
//  unchanged (resampling factor will still be applied, if specified); a 
//  value >0 changes the number of cells and overrides the resampling factor 
//  (if specified).
//  Currently, only integer refactorings are supported, so the node will fail
//  if num_cells is not a multiple or a factor of the original request's 
//  resolution.
//defrec end

namespace Meq {    

//##ModelId=400E530400A3
class ModRes : public Node
{
public:
    //##ModelId=400E5355029C
  ModRes();

    //##ModelId=400E5355029D
  virtual ~ModRes();

	virtual TypeId objectType() const
	{ return TpMeqModRes; }


protected:
  virtual void setStateImpl (DMI::Record::Ref &rec,bool initializing);

  virtual int  pollChildren (Result::Ref &resref,
                             const Request &req);
    
  virtual int getResult (Result::Ref &resref, 
                         const std::vector<Result::Ref> &childres,
                         const Request &req,bool newreq);
  
private:
  // operations specified via state are cached here
  //std::vector<int> factor;
  //std::vector<int> numcells;

  // the operations are then re-mapped into Cells constructor
  // arguments, which are stored here
  //int cells_op[Axis::MaxAxis];
  //int cells_arg[Axis::MaxAxis];
  //bool has_ops;

  int nx_,ny_;
  int do_resample_;
  
  // symdeps generated by ModRes
  vector<HIID>    res_symdeps_;
  int             res_depmask_;
  
  // if =0, res depmask is incremented
  // if !=0, res depmask is assigned with this index directly
  int   res_index_;
};


} // namespace Meq

#endif

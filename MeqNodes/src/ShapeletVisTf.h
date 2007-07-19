//# ShapeletVisTf.h: modifies request resolutions
//#
//# Copyright (C) 2002-2007
//# ASTRON (Netherlands Foundation for Research in Astronomy)
//# and The MeqTree Foundation
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
//# $Id: ShapeletVisTf.h,v 1.11 2006/05/30 16:44:32 sarod Exp $

#ifndef MEQNODES_SHAPELETVISTF_H
#define MEQNODES_SHAPELETVISTF_H
    
#include <MEQ/Node.h>
#include <MEQ/Cells.h>
#include <MEQ/AID-Meq.h>

#include <MeqNodes/TID-MeqNodes.h>

#include <shapelet.h>
#pragma aidgroup MeqNodes
#pragma types #Meq::ShapeletVisTf 
#pragma aid Filename Cutoff

// The comments below are used to automatically generate a default
// init-record for the class 

//defrec begin MeqShapeletVisTf
//  Changes the resolution of a parent's Request before passing it on to the
//  child. Returns child result as is. Expects exactly one child.
//field: children []
//  UV children, modes
//
//defrec end

namespace Meq {    

//##ModelId=400E530400A3
class ShapeletVisTf : public Node
{
public:
    //##ModelId=400E5355029C
  ShapeletVisTf();

    //##ModelId=400E5355029D
  virtual ~ShapeletVisTf();

	virtual TypeId objectType() const
	{ return TpMeqShapeletVisTf; }


protected:
  virtual void setStateImpl (DMI::Record::Ref &rec,bool initializing);

  virtual int getResult (Result::Ref &resref, 
                         const std::vector<Result::Ref> &childres,
                         const Request &req,bool newreq);
  
private:
  // symdeps generated by ModRes
  vector<HIID>    res_symdeps_;
  int             res_depmask_;
	vector<HIID>    seq_symdeps_;
	int             seq_depmask_;

	// if =0, res depmask is incremented
	// if !=0, res depmask is assigned with this index directly
	int   res_index_;

	//
	string filename_;
	//decomposition params
	int n0_;
	double beta_;
	blitz::Array<double,2> md_;//array of modes

	//cutoff weak modes
	double cutoff_;

};


} // namespace Meq

#endif

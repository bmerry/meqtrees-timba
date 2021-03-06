//# DataConcat.h: Class to visualize data
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

#ifndef MEQNODES_DATACONCAT_H
#define MEQNODES_DATACONCAT_H
    
#include <MEQ/Node.h>
#include <MEQ/VellSet.h>
#include <MeqNodes/TID-MeqNodes.h>
#include <MeqNodes/DataCollect.h>

#pragma types #Meq::DataConcat
#pragma aid Top Label Plot Data Skeleton

namespace Meq {

class Request;


class DataConcat : public Node
{
public:

  DataConcat();
    
  virtual ~DataConcat();

  virtual TypeId objectType () const { return TpMeqDataConcat; }

protected:
  //## override this, since we poll children ourselves
  virtual int getResult (Result::Ref &resref, 
                         const std::vector<Result::Ref> &childres,
                         const Request &req,bool newreq);

  virtual void setStateImpl (DMI::Record::Ref &rec,bool initializing);
  
  HIID top_label_;
  
  ObjRef attrib_;
};


} // namespace Meq

#endif

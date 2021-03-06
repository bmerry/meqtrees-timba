//#  tStringUtil.cc: test program for the string utilities class
//#
//#  Copyright (C) 2002-2007
//#  ASTRON (Netherlands Foundation for Research in Astronomy)
//#  and The MeqTree Foundation
//#  P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
//#
//#  This program is free software; you can redistribute it and/or modify
//#  it under the terms of the GNU General Public License as published by
//#  the Free Software Foundation; either version 2 of the License, or
//#  (at your option) any later version.
//#
//#  This program is distributed in the hope that it will be useful,
//#  but WITHOUT ANY WARRANTY; without even the implied warranty of
//#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//#  GNU General Public License for more details.
//#
//#  You should have received a copy of the GNU General Public License
//#  along with this program; if not, write to the Free Software
//#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//#
//#  $Id$

#include <TimBase/StringUtil.h>
#include <iostream>

using namespace LOFAR;
using namespace std;

int main()
{
  string s(",aa,bb,,dd,");
  vector<string> vs = StringUtil::split(s,',');
  cout << "Splitting string \"" << s << "\" using \',\' as seperator ..." 
       << endl;
  for (string::size_type i = 0; i < vs.size(); i++) {
    cout << "vs[" << i << "] = \"" << vs[i] << "\"" << endl;
  }
  return 0;
}

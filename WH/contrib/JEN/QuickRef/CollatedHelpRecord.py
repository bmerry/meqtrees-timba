# file: ../JEN/demo/CollatedHelpRecord.py:
#
# Author: J.E.Noordam
#
# Short description:
#
# History:
#   - 03 june 2008: creation (from QuickRef.py)
#
# Remarks:
#
# Description:
#


 
#********************************************************************************
# Initialisation:
#********************************************************************************

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

#=================================================================================

class CollatedHelpRecord (object):
   """This object collects and handles a hierarchical set of help strings
   into a record. This is controlled by the path, e.g. 'QuickRef.MeqNodes.unops'.
   """

   def __init__(self, name='CollatedHelpRecord', chrec=None):
      self._name = name 
      self.clear()
      if isinstance(chrec, record):
          self._chrec = chrec
      return None

   def clear (self):
      self._chrec = record(help=None, order=[])
      self._folder = record()
      return None

   def chrec (self):
      return self._chrec

   #---------------------------------------------------------------------

   def insert_help (self, path=None, help=None, rr=None, level=0, trace=False):
      """Insert a help-item at the designated (path) position (recursive)
      """
      if level==0:
         rr = self._chrec

      if isinstance(path,str):
         path = path.split('.')

      key = path[0]
      if not rr.has_key(key):
         rr.order.append(key)
         rr[key] = record(help=None)
         if len(path)>1:
            rr[key].order = []

      if len(path)>1:                        # recursive
         self.insert_help(path=path[1:], help=help, rr=rr[key],
                          level=level+1, trace=trace)
      else:
         rr[key].help = help                 # may be list of strings...
         if trace:
            prefix = self.prefix(level)
            print '.insert_help():',prefix,key,':',help
      # Finished:
      return None

   #---------------------------------------------------------------------
   
   def prefix (self, level=0):
      """Indentation string"""
      ps= ' '+(level*'..')+' '
      # ps= ' '+str(level)+(level*'..')+' '
      return ps

   #---------------------------------------------------------------------

   def show(self, txt=None, rr=None, full=False, key=None, level=0):
      """Show the record (recursive)"""
      if level==0:
         print '\n** CHR.show(',txt,', full='+str(full),'):',str(self._name)
         rr = self._chrec
      prefix = self.prefix(level)

      if not rr.has_key('order'):                # has no 'order' key
         for key in rr.keys():
            if isinstance(rr[key], (list,tuple)):
               if len(rr[key])>1:
                  print prefix,key,':',rr[key][0]
                  for s in rr[key][1:]:
                     print prefix,len(key)*' ',s
               else:
                  print prefix,key,':',rr[key]
            else:
               print prefix,key,'(no order):',type(rr[key])

      else:                                      # has 'order' key
         for key in rr.keys():
            if isinstance(rr[key], (list,tuple)):
               if key in ['order']:              # ignore 'order'
                  if full:
                     print prefix,key,':',rr[key]
               elif len(rr[key])>1:
                  print prefix,key,':',rr[key][0]
                  for s in rr[key][1:]:
                     print prefix,len(key)*' ',s
               else:
                  print prefix,key,'(',len(rr[key]),'):',rr[key]
            elif not isinstance(rr[key], (dict,Timba.dmi.record)):
               print prefix,key,'(',type(rr[key]),'??):',rr[key]
               
         for key in rr['order']:
            if isinstance(rr[key], (dict,Timba.dmi.record)):
               self.show(rr=rr[key], key=key, level=level+1, full=full) 
            else:
               print prefix,key,'(',type(rr[key]),'??):',rr[key]

      if level==0:
         print '**\n'
      return None


   #---------------------------------------------------------------------

   def format(self, rr=None, ss=None, key=None, level=0, trace=False):
      """
      Recursively format a help-string, to be printed.
      """
      if level==0:
         ss = '\n'
         rr = self._chrec
         if trace:
            print '\n** Start of .format():'
            
      prefix = '\n'+self.prefix(level)

      # First attach the overall help, if available:
      if rr.has_key('help'):
         help = rr['help']
         if isinstance(help, str):
            ss += prefix+str(help)
         elif isinstance(help, (list,tuple)):
            ss += prefix+str(help[0])
            if len(help)>1:
               # s1 = str(len(str(key))*' ')           # keys too long...
               s1 = str(5*' ')                        # <---- !!
               for s in help[1:]:
                  ss += prefix+s1+str(s)

      # Then recurse in the proper order, if possible:
      keys = rr.keys()
      if rr.has_key('order'):                # has no 'order' key
         keys = rr['order']
      for key in keys:
         if isinstance(rr[key], (dict,Timba.dmi.record)):
            ss = self.format(rr=rr[key], ss=ss, key=key,
                             level=level+1, trace=trace) 
      # Finished:
      if len(keys)>1:
         ss += prefix
      if level==0:
         ss += '**\n'
         if trace:
            print '\n** End of .format():\n'
            print ss
      return ss

   #---------------------------------------------------------------------

   def save (self, filename='CollatedHelpString', rr=None):
      """Save the formatted help-string in the specified file"""
      if not '.' in filename:
         filename += '.meqdoc'
      file = open (filename,'w')
      ss = self.format()
      file.writelines(ss)
      file.close()
      print '\n** Saved the doc string in file: ',filename,'**\n'
      return filename
      

   #---------------------------------------------------------------------

   def subrec(self, path, trace=False):
      """Extract (a deep copy of) the specified (path) subrecord
      from the internal self._chrec.
      """
      if trace:
         print '\n** .extract(',path,'):'

      rr = copy.deepcopy(self._chrec)
      ss = path.split('.')
      for key in ss:
         if trace:
            print '-',key,ss,rr.keys()
         if not rr.has_key(key):
            s = '** key='+key+' not found in: '+str(ss)
            raise ValueError,s
         else:
            rr = rr[key]

      # Return another object of the same type:
      newname = 'subrec('+path+')'
      result = CollatedHelpRecord(newname, chrec=rr)
      if trace:
         result.show(txt=path)
      return result
      
   #---------------------------------------------------------------------

   def cleanup (self, rr=None, level=0, trace=False):
      """Return a cleaned-up copy of its internal record.
      """
      if level==0:
         if trace:
            print '\n** .cleanup():'
         rr = copy.deepcopy(self._chrec)
            
      if isinstance(rr, dict):
         if rr.has_key('order'):
            rr.__delitem__('order')                   # remove the order field
            for key in rr.keys():
               if isinstance(rr[key], dict):          # recursive
                  rr[key] = self.cleanup(rr=rr[key], level=level+1)

      if level>0:
          # Not finished: Return to former level:
          return rr

      # Finished: eturn another object of the same type:
      newname = 'upcleaned'
      result = CollatedHelpRecord(newname, chrec=rr)
      if trace:
          print '** finished .cleanup()'
      return result


   #---------------------------------------------------------------------

   def bookmark (self, path, trace=False):
      """A little service to determine [page,folder] from path.
      It is part of this class because it initializes each time.
      This is necessary to avoid extra pages/folders.
      """
      # trace = True
      ss = path.split('.')
      nss = len(ss)

      page = None
      page = ss[nss-1]                          # the last one, always there
      if nss>1:
         page = ss[nss-2]+'_'+ss[nss-1]

      folder = None
      if len(ss)>3:
         folder = ss[nss-3]+'_'+ss[nss-2]       # same format as page above (essential!)

      if folder:
         self._folder.setdefault(folder,0)
         self._folder[folder] += 1
      elif page and self._folder.has_key(page):
         folder = page                          # works well for ...resampling_modres....
         self._folder[folder] += 1              # ....?
         # page = None                            # produces 'autopage' pages in the folder
         # page = '..dummy..'                     # still there, clean up later

      # Finished:
      if trace:
         print '*** .bookmark():',len(ss),ss,' page=',page,' folder=',folder
      return [page,folder]







#=====================================================================================
# Standalone test (without the browser):
#=====================================================================================

if __name__ == '__main__':

   print '\n** Start of standalone test of: CollatedHelpRecord.py:\n' 
   from Timba.TDL import *
   from Timba.Meq import meq
   ns = NodeScope()

   if 1:
      rider = CollatedHelpRecord()

   if 0:
      path = 'aa.bb.cc.dd'
      help = 'xxx'
      rider.insert_help(path=path, help=help, trace=True)

   if 1:
      import QR_MeqNodes
      QR_MeqNodes.MeqNodes(ns, 'test', rider=rider)
      # rider.show('testing', full=True)
      # print rider.format()

      if 1:
         path = 'test.MeqNodes.binops'
         # path = 'test.MeqNodes'
         sub = rider.subrec(path, trace=True)
         sub.show(full=False)
         sub.show(full=True)
         sub.format(trace=True)

         if 0:
            clean = sub.cleanup(trace=True)
            # The order fields should now have disappeared: (no order)
            clean.show(full=True)
            # Finally, test whether the original self._chrec still has order fields:
            sub.show('after cleanup', full=True)
            
   print '\n** End of standalone test of: CollatedHelpRecord.py:\n' 

#=====================================================================================



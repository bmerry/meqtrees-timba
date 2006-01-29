# JEN_inarg.py:
#
# Author: J.E.Noordam
#
# Short description:
#    Functions dealing with records of input arguments
#
# History:
#    - 04 dec 2005: creation
#    - 11 dec 2005: ready for use with MG_JEN_Joneset.py
#    - 13 dec 2005: added .clone()
#    - 15 dec 2005: included ._replace_reference() in .attach()
#    - 16 dec 2005: included version keyword in .inarg2pp()
#    - 14 jan 2006: added .dissect_target()
#    - 14 jan 2006: made _replace_reference() react to '@' and '@@'
#
# Full description:
#    By obeying a simple (and unconstraining!) set of rules, the input
#    arguments of any function may be manipulated as a record. This has
#    many advantages:
#
#    -) The inarg argument record is guaranteed to be uptodate
#       (use the versioning keyword)
#    -) Arguments can be referred to other arguments by name
#       (thus, when one is modified, the other will follow)
#    -) It can be manipulated independently of the function
#       -) It can be combined (hierarchically) with others
#       -) Argument values may be modified recursively
#       -) It can be used for batch processing
#       -) It can be modified in a gui
#    -) Template specification modules may be copied from the
#       script in which the inarg-compatible function is defined.
#       These templates are designed in such a way that: 
#       -) Argument modification statements can be commented out
#          This allows a visible choice of alternatives
#       -) Helpful suggestions may be inserted as comments
#       -) Various alternative templates are possible for the same function
#
#    An 'inarg-compatible' function has the following general structure:
#
#        def myfunc(x=None, y=None, **inarg):
#
#            # The part that deals with the input arguments:
#            pp = JEN_inarg.inarg2pp(inarg, 'myfunc', version='15dec2005')
#            pp.setdefault('aa', value1)
#            pp.setdefault('bb', value2)
#            if JEN_inarg.getdefaults(pp): return JEN_inarg.pp2inarg(pp)
#
#            # The function body, which uses the values in record pp:
#            result = .... 
#            return result
#
#    An inarg-compatible function may be used in the following manner: 
#    1) First obtain an inarg record with default arguments by:
#            inarg = myfunc(_getdefaults=True)
#    2) Execute it by:
#            result = myfunc(_inarg=inarg)
#    Thus, there are two reserved keywords (_getdefaults and _inarg), which should
#    not be used for actual arguments. 
#    Note that the function can still be called in a traditional way also:
#            result = myfunc(aa=4)
#
#    The default values in an inarg record may be modified in several ways:
#    1) By a special function (recursive!):
#            JEN_inarg.modify(inarg, bb=56)
#    2) By extra keyword arguments when obtaining the inarg record:
#            inarg = myfunc(_getdefaults=True, aa='something', bb='other')
#    3) By extra keyword arguments when executing myfunc():
#            result = myfunc(x=1, y=-2, _inarg=inarg, bb=-78)
#    In all cases, the keywords have to exist. Only .modify() is recursive,
#    so it also searches a hierarchy of nested inargs (and modifies all levels!).
#    The other two only search the top level of the input inarg. 
#
#    An inarg-record has the following (hierarchical!) structure:
#    - JEN_inarg_CTRL_record:
#    - module1::func1()
#    - module1::func2()
#      - module2::func3()
#        - module4::func5()
#      - module3::func4()
#    - module2::func3()
#    - etc
#
#    An inarg-record contains at least one inarg-module:
#    - module1::func1()
#      - keyword1 = value1
#      - keyword2 = value2
#      - ...
#      - JEN_inarg_CTRL_record:
#
#    1) The module name uniquely identifies the relevant inarg-compatible function.
#       This name is defined inside the function itself.
#    2) A set of zero or more input argument values (keyword=value)
#    3) A control-record, with the following fields:
#       - localscope (required): (see .localscope())
#       - scope (required): localscope without qualifier
#       - qualifier (optional): (see .qualifier() and .clone())
#       - nested (optional): indicates whether the function is nested
#       - ERROR (optional): record with error messages (see .ERROR())
#       - WARNING (optional): record with warning messages (see WARNING())
#       - MESSAGE (optional): record with general messages (see .MESSAGE())
#       - etc
#
#    Inside myfunc(), the function JEN_inarg.inarg2pp(inarg, funcname) does the following:
#    1) If inarg has a field '_getdefaults': It returns pp=dict()
#    2) If inarg has a field '_inarg': It looks for a field in with the correct localscope,
#       and extracts it as an 'interal' argument record pp.
#    3) Otherwise:
# 
#    Optional extras:
#    1) .clone(inarg, _qual=...):
#    2) .init(funcname, **opt)

#================================================================================
# Preamble
#================================================================================

from Timba.TDL import *
from Timba.Trees import JEN_record

from copy import deepcopy
from datetime import datetime

# The name of the control-record
CTRL_record = '_JEN_inarg_CTRL_record:'

# The name of an (optional) option field (e.g. see .modify())
option_field = '_JEN_inarg_option'

#----------------------------------------------------------------------------

def init(target='<target>', version='15dec2005', **pp):
   """Initialise a valid inarg record, with optional fields **pp.
   This is done when starting a composite inarg record, e.g. in MG_JEN_xxx.py"""

   # Deal with the keyword arguments:
   if not isinstance(pp, dict): pp = dict()     # overkill?
   inarg = pp                                   # default is empty dict                       
   inarg['script_name'] = target                # expected in MG control record (kludge...)

   _ensure_CTRL_record(inarg, target, version=version)

   trace = False
   if trace: display(inarg, 'JEN_inarg.init()', full=True)
   # Return the inarg record:
   return inarg


#----------------------------------------------------------------------------

def TDL_record(rr, level=0):
   """Convert the given dict/record (rr) into a TDL record"""
   if not isinstance(rr, dict): return rr                     #.....??
   cc = record()
   trace = False
   if trace: s1 = _prefix(level)
   for key in rr.keys():
      if isinstance(rr[key], dict):
         cc[key] = TDL_record(rr[key], level=level+1)
      else:
         cc[key] = rr[key]
      if trace: print s1,key,':',type(rr[key]),' -> ',type(cc[key])
   return cc


#----------------------------------------------------------------------------

def is_inarg(rr, origin='...', level=0, trace=False):
   """Test whether rr is an external (or internal) argument record"""
   if not isinstance(rr, dict): return False        # record is a dict too
   # Look for a valid CTRL record:
   if rr.has_key(CTRL_record):
      if isinstance(rr[CTRL_record], dict): return True
      return False                                  # ...??
   # Recursive:
   for key in rr.keys():
      if isinstance(rr[key], dict):
         if is_inarg(rr[key], level=level+1, trace=trace): return True
   return False

#----------------------------------------------------------------------------

def is_OK(rr, trace=False):
   """Generic test whether rr (pp or inarg) is ok"""
   if count(rr, 'ERROR')>0: return False
   if count(rr, 'WARNING')>0: return False
   return True

def is_OK_old(rr, level=0, trace=False):
   """Generic test whether rr (pp or inarg) is ok"""
   if not isinstance(rr, dict):
      return False
   for key in rr.keys():
      if key==CTRL_record:
         if not isinstance(rr[key], dict): return False
         if rr[key].has_key('ERROR'): return False
         if rr[key].has_key('WARNING'): return False
      elif isinstance(rr[key],dict):                    # recursive
         ok = is_OK(rr[key], level=level+1, trace=trace)
         if not ok: return False
   return True

#----------------------------------------------------------------------------

def _prefix(level=0):
   """Make a level-dependent message prefix (for tracing recursion)"""
   prefix = '  '+str(level)+': '+(level*'..')
   return prefix

#----------------------------------------------------------------------------

def clone(inarg, _qual=None, trace=False):
   """Copy the input inarg, and qualify its localscope (mandatory!).
   This is used to make multiple inargs for the same function"""
   if trace:
      display(inarg, 'JEN_inarg.clone('+str(_qual)+') input', full=True)
   if not isinstance(inarg, dict): return False

   # A (unique) qualifier is mandatory:
   if _qual==None: return False

   rr = deepcopy(inarg)

   # Keep (accumulated) qualifier also
   _qual = '['+str(_qual)+']'                  # make qualifier string
   oldqual = qualifier(rr)                     # get the current one (if any)
   newqual = oldqual+_qual                     # append the new qualifier
   CTRL(rr,'qualifier', newqual)               # replace

   # Change the localscope:
   oldscope = localscope(rr)                   # get the current localscope
   newscope = oldscope+_qual                   # append the qualifier
   CTRL(rr,'localscope', newscope)             # replace

   # Change the field name in rr:
   if rr.has_key(oldscope):
      rr[newscope] = rr[oldscope]
      rr.__delitem__(oldscope)

   if trace:
      display(rr, 'rr <- JEN_inarg.clone('+str(_qual)+')', full=True)
   return rr

#============================================================================

def modify(inarg, **arg):
   """Recursively modify the values of the specified (**arg) fields"""
   trace = False
   if trace: print '\n** JEN_inarg.modify(): ',arg
   if not is_inarg(inarg): return False
   if not isinstance(arg, dict): return False

   # Deal with the option feld (if any):
   if arg.has_key(option_field):                     # has an option field
      # ..... placeholder for later ....
      MESSAGE(inarg,'.modify(): stripped off: '+option_field)
      arg.__delitem__(option_field)                  # just strip it off

   # Keep track of whether the keywords are found (see also below):
   found = dict()
   for key in arg.keys(): found[key] = 0

   # The actual work: recursive modification:
   _modify_level(inarg, arg=arg, found=found, trace=trace)
   MESSAGE(inarg,'.modify(): found ='+str(found))

   # Check the result:
   ok = True
   for key in found.keys():
      if not found[key]:
         ok = False
   if not ok:
      ERROR(inarg,'.modify(): NOT ok: (found ='+str(found)+')')
      trace = True

   if trace:
      print '** found =',found,': ok =',ok
      display(inarg,'<= JEN_inarg.modify()',full=True)
   return ok

#----------------------------------------------------------------------------

def _modify_level(rr, arg, found, level=0, trace=False):
   """Recursive function that does the work for .modify()"""
   fname = localscope(rr)
   # s0 = _prefix(level)
   
   # First replace the fields at this level (if present):
   for key in arg.keys():
      if rr.has_key(key):                        # key exists in rr[fname]
         found[key] += 1                         # increment
         s1 = '.modify( '+key+' ): '
         if not rr[key]==arg[key]:               # different value
            was = rr[key]
            rr[key] = arg[key]                   # replace with new value
            s1 += str(was)+'  ->  '+str(rr[key])
            MESSAGE(rr,s1)
         else:
            s1 += ' (unchanged) = '+str(rr[key])
            # MESSAGE(rr,s1)

   # Recursive:
   for key in rr.keys():
      if isinstance(rr[key], dict):
         if not key==CTRL_record:                # ignore CTRL_record
            _modify_level(rr[key], arg=arg, found=found, level=level+1, trace=trace)

   return True


#============================================================================

def dissect_target (target='<dir>/<module>::<function>()', qual=None, trace=False):
   """Dissect the input string into fields of a record"""
   rr = dict(target_definition=target,
             target_function='<target_function>',
             target_module='<target_module>',
             target_dir='.',
             qual=qual,
             localscope='<localscope>',
             barescope='<barescope>')

   if trace: print '** .dissect_target(',target,'):'
   # Get the target directory (if any):
   ss = target.split('/')
   if len(ss)>1:
      rr['target_dir'] = ss[0]
      target = ss[len(ss)-1]

   # Get the target module (if any):
   ss = target.split(':')
   if len(ss)==3:                                     # split on ::
      rr['target_module'] = ss[0]
      rr['target_function'] = ss[2]
      target = ss[len(ss)-1]
   ss = target.split('.')
   if len(ss)>1:                                      # split on .
      rr['target_module'] = ss[0]
      target = ss[len(ss)-1]

   # The naked name of the target function:
   rr['target_function'] = target.split('(')[0]       # remove any ()

   # The localscope is the inarg record field-name:
   rr['localscope'] = '**** '
   rr['localscope'] = ''
   rr['localscope'] += rr['target_dir']+'/'
   rr['localscope'] += rr['target_module']+'.'
   rr['localscope'] += rr['target_function']+'()'
   if qual:                                           # qualifier specified
      rr['localscope'] += '['+str(qual)+']'

   # The barescope is a stripped version of the localscope:
   rr['barescope'] = rr['target_module']+rr['target_function']

   # Finished:
   if trace: print '    ->',rr
   return rr


def _ensure_CTRL_record(rr, target='<target>', version=None, qual=None):
   """Make sure that rr has a valid JEN_inarg_CTRL record"""

   if not isinstance(rr, dict):
      print '\n** _ensure_CTRL_record(rr): rr not a dict, but: '+str(type(rr)),'\n'
      return False

   if not rr.has_key(CTRL_record):                    # rr does NOT have a CTRL record yet
      ctrl = dissect_target (target, qual=qual)
      ctrl['version'] = version
      now = str(datetime.now())
      ctrl['datetime_defined'] = now                  # not modified anymore
      ctrl['last_edited'] = now                       # updated in inargGUI
      ss = 'CTRL: '+ctrl['target_function']
      ctrl['oneliner'] = ss
      ctrl['order'] = [CTRL_record]                   # order of fields
      ctrl['protected'] = False                       # if True, cannot be edited...
      rr[CTRL_record] = ctrl                          # Attach the CTRL_record

   elif not isinstance(rr[CTRL_record], dict):        # CTRL_record is not a record...??
      ERROR(rr,'inarg/pp['+CTRL_record+'] not a dict, but: '+str(type(rr[CTRL_record])))

   else:                                              # rr already has a valid CTRL_record
      if version:                                     # version has been specified (.inarg2pp())
         #===================================================
         # return True                # temporarily disabled!!!
         #===================================================
         # The version keyword allows detecton of obsolete inarg records:
         rr_version = rr[CTRL_record]['version']
         if not rr_version==version:
            ERROR(rr,'inarg/pp version mismatch: '+rr_version+' != '+version)
            return False                              # then what....?
   return True
   
#----------------------------------------------------------------------------

def CTRL(rr, key=None, value=None, delete=None, report=True,
         recurse=True, level=0, trace=False):
   """Access to JEN_inarg_CTRL_record. If no key specified, get the (first!)
   JEN_inarg_CTRL_record field from rr (if any).
   If a field (key) is specified, return its value instead.
   If a value is specified, modify the field value first"""

   if not isinstance(rr, dict):
      return False

   elif not rr.has_key(CTRL_record):          # recursive....!!
      if recurse:
         for key1 in rr.keys():
            if isinstance(rr[key1],dict):
               return CTRL(rr[key1], key=key, value=value, delete=delete,
                           recurse=recurse, level=level+1,
                           report=report, trace=trace)

   else:                                      # CTRL record found
      s1 = 'JEN_inarg_CTRL(level='+str(level)+')'
      cc = rr[CTRL_record]                    # convenience
      if not isinstance(cc, dict):
         if trace: print s1,'not a record, but:',type(cc)
      elif not key:                           # no key specified
         if trace: display(cc,'JEN_inarg_CTRL <- '+s1)
         return cc                            # return the entire CTRL record                         
      elif not value==None:                   # new value specified
         was = 'noexist'
         if cc.has_key(key): was = cc[key]
         rr[CTRL_record][key] = value
         if trace: print s1,key,':',was,'->',rr[CTRL_record][key]
         return rr[CTRL_record][key]          # return new current value
      elif not cc.has_key(key):               # no such field
         if trace: print s1,'no such key:',key,' (in:',cc.keys(),')'
         if delete: return False              # ok
      elif delete:                            # delete the field
         if trace: print s1,'deleted key:',key,' (was:',cc[key],')'
         rr[CTRL_record].__delitem__(key)
         return rr[CTRL_record].has_key(key) 
      else:
         if trace: print s1,key,'=',cc[key]
         return cc[key]                       # return current value

   if level==0:
      if report: print '** JEN_inarg.CTRL(',key,value,'): not found'
   return None

#----------------------------------------------------------------------------

def localscope(rr, trace=False):
   """Get the localscope (funcname+qualifiers) from the CTRL record or rr"""
   lscope = CTRL(rr, 'localscope')
   if trace: print '.localscope() ->',type(lscope),len(lscope),'=',lscope
   return lscope

def qualifier(rr, trace=False):
   """Get the localscope (funcname+qualifiers) from the CTRL record or rr"""
   qual = CTRL(rr, 'qualifier', report=False)
   if qual==None: qual = ''                   # empty string
   if trace: print '.qualifier() ->',type(qual),len(qual),'=',qual
   return qual

def barescope(rr, trace=False):
   """Get the funcname (localscope without qualifiers) from the CTRL record or rr"""
   bs = CTRL(rr, 'barescope')
   if trace: print '.barescope() ->',type(bs),len(bs),'=',bs
   return bs

#----------------------------------------------------------------------------

def ERROR(rr, txt=None, clear=False, trace=False):
   """Interact with the ERROR record of the JEN_inarg_CTRL field"""
   return MESSAGE(rr, txt=txt, field='ERROR', clear=clear, trace=trace)

def WARNING(rr, txt=None, clear=False, trace=False):
   """Interact with the WARNING record of the JEN_inarg_CTRL field"""
   return MESSAGE(rr, txt=txt, field='WARNING', clear=clear, trace=trace)

def HISTORY(rr, txt=None, clear=False, trace=False):
   """Interact with the HISTORY record of the JEN_inarg_CTRL field"""
   txt = str(datetime.now())+': '+str(txt)
   return MESSAGE(rr, txt=txt, field='HISTORY', clear=clear, trace=trace)

def MESSAGE(rr, txt=None, field='MESSAGE', clear=False, trace=False):
   """Interact with the specified record of the JEN_inarg_CTRL field"""
   s1 = 'JEN_inarg.'+field+'():'
   if clear:                                     # clear the record
      CTRL(rr,field,delete=True, trace=trace)
   if txt:                                       # message specified
      cc = CTRL(rr,field,report=False, trace=trace)  # check existence
      if not cc: cc = dict()
      cc[str(len(cc))] = txt
      if field in ['ERROR','WARNING']:
         print '\n**',s1,localscope(rr),'(total=',len(cc),'):',txt,'\n'
      cc = CTRL(rr,field,cc, trace=trace)      
   if trace:
      display(rr,s1, full=True)
   return CTRL(rr,field,trace=trace)      

#------------------------------------------------------------------------------

def view(rr, field='MESSAGE', ss='', level=0, trace=True):
   """View (recursively) the specified JEN_inarg_CTRL field entries"""
   if level==0:
      s = '\n** Recursive view of inarg CTRL_record field: '+field
      if trace: print s
      ss = s
   if isinstance(rr, dict):
      # Get the specified field of the CTRL_record (if any):
      cc = CTRL(rr, field, report=False, recurse=False) 
      if isinstance(cc, dict):
         # Show the dict entries in the correct order:
         for i in range(len(cc)):
            s = _prefix(level)+' - '+str(i)+':  '+cc[str(i)]
            if trace: print s
            ss += '\n'+s
      # Recursive:
      for key in rr.keys():
         if isinstance(rr[key], dict):
            if not key==CTRL_record:
               s = _prefix(level+1)+' ***** '+key+':'
               if trace: print s
               ss += '\n'+s
               ss = view(rr[key], field=field, ss=ss, level=level+1, trace=trace)
   if level==0:
      ok = is_OK(rr)
      if ok: s = '** end of view of: '+field+'   (OK)\n'
      if not ok: s = '** end of view of: '+field+'                   .... NOT OK ....!!\n'
      if trace: print s
      ss += '\n'+s
   return ss

#------------------------------------------------------------------------------

def count(rr, field='MESSAGE', total=0, level=0):
   """Count (recursively) the specified JEN_inarg_CTRL fields"""
   if isinstance(rr, dict):
      # Get the specified field of the CTRL_record (if any):
      cc = CTRL(rr, field, report=False, recurse=False) 
      if isinstance(cc, dict):
         total += len(cc)
      # Recursive:
      for key in rr.keys():
         if isinstance(rr[key], dict):
            if not key==CTRL_record:
               total = count(rr[key], field=field, total=total, level=level+1)
   return total


#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def display(rr, txt=None, name=None, full=False):
   """Display the argument record (inarg or pp)"""
   if not isinstance(rr, dict):
      print '** JEN_inarg.display(rr): not a record, but:',type(rr)
      return False
   if not name:                                        # Make sure of name
      name = 'rr'
      if is_inarg(rr): name = 'inarg/pp'               # argument record

   # Work on a copy (qq):
   qq = rr
   if not is_OK(qq): full = True
   if not full:
      qq = _strip(rr, CTRL_record)                     # remove CTRL fields

   # Do the display:
   JEN_record.display_object(qq,name, txt, full=full)
   if not full:
      print '** NB: The JEN_inarg_CTRL records are not shown.\n'
   return True


#----------------------------------------------------------------------------

def _strip(rr, key=CTRL_record, level=0, trace=False):
   """Strip off all instances of the named (key) field from record rr"""
   if not isinstance(rr, dict): return rr
   qq = deepcopy(rr)
   # Remove the named field if present:
   if qq.has_key(key):
      print _prefix(level),'_strip(',key,'): ',localscope(qq)
      qq.__delitem__(key)
   # Recurse:
   for key1 in qq.keys():
      if isinstance(qq[key1], dict):
         qq[key1] = _strip(qq[key1], key=key, level=level+1, trace=trace)
   return qq

#----------------------------------------------------------------------------

def getdefaults(pp, check=True, strip=False, trace=False):
   """The function that decides whether its calling function is to be executed
   (and then checks and prepares the argument record pp), or whether it should
   just return an inarg record with default values. This is controlled by the
   presence of a '_getdefaults' field in the internal argument record pp""" 
   if trace:
      display(pp,'input pp to .getdefaults(pp)', full=True)

   if not isinstance(pp, dict):
      print '** JEN_inarg.getdefaults(pp): pp not a record, but:',type(pp) 
      return False                      # ....?

   if pp.has_key('_getdefaults'):
      # Use: if JEN_inarg.getdefaults(pp): return JEN_inarg.pp2inarg(pp)
      # i.e. if True, do NOT execute the body of the mother function,
      #      but just return an inarg record with its default arguments
      return True

   #....................................................................
   #....................................................................

   # Replace referenced values (if any):
   # NB: This should be done ONLY to the executed pp-record, of course...!
   _replace_reference(pp, trace=trace)

   if check:
      # At the very least, report any problems:
      if not is_OK(pp):
         display(pp,'.getdefaults(): NOT OK!!')
         return True                              # do NOT execute....

   # trace = True              # ALWAYS show pp to be executed
   if trace:
      lscope = localscope(pp)
      display(pp,'pp to be executed for: '+lscope, full=True)

   # strip = True              # ALWAY strip, but AFTER display.....?
   if strip:
      # Optionally, strip off the JEN_inarg_CTRL record:
      pp = _strip(pp, CTRL_record, trace=trace)
      
   # Return False to cause the calling function to execute its body:
   return False
   
#----------------------------------------------------------------------------

def _replace_reference(rr, acc=dict(), repeat=0, level=0, trace=False):
   """If the value of a field in the given record (rr) is referenced to:
   - a field name (prepended with @) in the same record
   - a field name (prepended with @@) in the parent record(s)
   replace it with the value of the referenced field"""

   trace = False
   
   if trace and level==0:
      print '\n** _replace_reference(',repeat,'):',type(rr)
   if not isinstance(rr, dict):
      return False
   if repeat>10:
      print 'JEN_inarg._replace_reference(): max repeat exceeded',repeat
      return False

   count = 0                               # replacement counter
   for key in rr.keys():                   # for all fields
      value = rr[key]                      # field value
      if key==CTRL_record:                 # ignore
         pass

      elif isinstance(value, dict):           # if field value is a dict
         # Append suitable arguments for upward reference (@@) to acc1:
         acc1 = deepcopy(acc)
         for key1 in rr.keys(): 
            if not isinstance(rr[key1], dict):
               if isinstance(rr[key1], str):
                  if not rr[key1][0]=='@':    # ignore referenced values
                     acc1[key1] = rr[key1]
               else:
                  acc1[key1] = rr[key1]
         if trace: print _prefix(level),acc1.keys()
         _replace_reference(rr[key], acc=acc1, level=level+1, trace=trace)

      elif isinstance(value, str):            # if field value is a string
         if trace: print _prefix(level),(level*'.'),':',key,'=',value
         if value[0]=='@':
            if value[1]=='@':
               vkey = value.split('@')[2]     # strip off the prepended '@@'
               qq = acc                       # search in acc (upwards)
            else:
               vkey = value.split('@')[1]     # strip off the prepended '@'
               qq = rr                        # search in rr

            if qq.has_key(vkey):              # if vkey is the name of another field
               if not value==qq[vkey]:        # different values
                  count += 1                  # count the number of replacements
                  s1 = _prefix(level)+'qq['+key+']: '+str(value)+' -> '+str(qq[vkey])
                  if trace: print s1
                  MESSAGE(rr, s1)
                  rr[key] = qq[vkey]          # replace with the value of the referenced field

   # Repeat this if necessary, i.e. if at least one value has been replaced
   # (This is because values may be multiply referenced)
   if count>0:
      _replace_reference(rr, acc=acc, repeat=repeat+1)
   if trace and level==0: print
   return count

#---------------------------------------------------------------------------

def _count_reference(rr, n=0, n1=0, n2=0, name='<name>', level=0, trace=False):
   """Count the nr of argument names prepended with @ or @@"""
   if level==0:
      if trace: print '\n** _count_reference():',type(rr)
   if not isinstance(rr, dict):
      return False
   for key in rr.keys():                   # for all fields
      value = rr[key]
      if key==CTRL_record:                 # ignore
         pass
      elif isinstance(value, dict):        # if field value is a dict
         qq = _count_reference(rr[key], n=n, n1=n1, n2=n2,
                               name=key, level=level+1, trace=trace)
         n = qq['n']
         n1 = qq['n1']
         n2 = qq['n2']
      elif isinstance(value, str):         # if field value is a string
         if value[0]=='@':
            n += 1                         # total nr
            if value[1]=='@':
               n2 += 1                     # nr of '@@...'
            else:
               n1 += 1                     # nr of '@...'
            if trace:
               print _prefix(level),n,n1,n2,':',key,'=',value,'  (',name,')'
   # Return the result as a record:
   if level==0:
      if trace: print 
   return dict(n=n, n1=n1, n2=n2)


#----------------------------------------------------------------------------
# This is the on_entry function of a inarg-compatible function.
#----------------------------------------------------------------------------

def inarg2pp(inarg, target='<target>', version='15jan2006', trace=False):
   """Extract the relevant internal argument record (pp) from inarg"""

   s0 = '** JEN_inarg.inarg2pp('+target+'): '
   # if trace: display(inarg,'input to .inarg2pp(inarg)', full=True)

   if not isinstance(inarg, dict):
      # Error (Difficult to imagine how this could happen....)
      if trace: print s0,'inarg not a dict'
      return inarg

   # Construct the localscope string (target+[qualifiers]):
   qual = None
   if inarg.has_key('_qual'):
      qual = inarg['_qual']
      inarg.__delitem__('_qual')
   localscope = dissect_target(target, qual=qual)['localscope']


   # Check for the existence of reserved keywords:
   if inarg.has_key('_getdefaults'):
      # Called as .func(_getdefaults=... [, _qual=...]), and results in default inarg.
      # NB: The call may contain other (overriding) keyword arguments too...
      if trace: print s0,'inarg has key _getdefaults'
      pp = inarg

   elif inarg.has_key('_inarg'):
      # Called as .func(_inarg=inarg [, _qual=...]): extract the internal pp record:
      s1 = '** JEN_inarg.inarg2pp(): '
      if not is_inarg(inarg['_inarg']):                        #...........??
         print s0,'inarg is not a valid inarg: ',type(inarg)
         return False

      elif not inarg['_inarg'].has_key(localscope):
         # Trying to run the function with the wrong inarg
         # (i.e. an inarg for a different funtion(s)) should result in an error:
         print '\n',s1,'inarg does not relate to function:',localscope
         print '  inarg.keys():',inarg.keys(),'\n'
         return False

      elif not isinstance(inarg['_inarg'][localscope], dict):
         # Trying to run the function with an invalid inarg[localscope] record
         # should result in an error:
         print s1,'inarg[',localscope,'] is not a record/dict, but:',type(inarg['_inarg'][localscope])
         return False

      else:
         # The main dish: inarg contains a record of argument values for the relevant
         # function. Detach it from inarg as a bare record pp:
         pp = inarg['_inarg'][localscope]
         # display(pp,'pp extracted from inarg')

         # Indicate that this particular sub-inarg will be executed
         # (this allows stripping off non-executed inarg records, to avoid clutter)
         if False:
            # NB: This give version clashes (requires more thought....)
            _ensure_CTRL_record(inarg['_inarg'][localscope], localscope)    # just in case....
            CTRL(inarg['_inarg'][localscope], 'executed', True)

         # Now deal with any EXTRA keyword arguments in inarg, which may have been
         # supplied as:     myfunc(_inarg=inarg, aa=10, bb=-13)
         # If recognised, these OVERRIDE the values of the relevant pp fields.
         # NB: Any extra arguments that are not fields in pp are ignored, and lost!
         
         for key in inarg.keys():
            if not key=='_inarg':
               if pp.has_key(key):
                  was = pp[key]
                  pp[key] = inarg[key]
                  MESSAGE(pp, s1+'overridden pp['+key+']: '+str(was)+' -> '+str(pp[key]))
               else:
                  MESSAGE(pp, s1+'ignored extra field inarg['+key+'] = '+str(inarg[key]))


   else:
      # Assume that the function has been called 'traditionally'
      pp = inarg
      if trace: print '-- inarg traditional'

   # Attach CTRL record to pp (if necessary):
   _ensure_CTRL_record(pp, target, version=version, qual=qual)

   if trace: display(pp,'pp <- .inarg2pp(inarg)', full=True)
   return pp




#----------------------------------------------------------------------------

def gui(inarg):
   """Placeholder for inarg specification GUI"""
   return False

#----------------------------------------------------------------------------

def pp2inarg(pp, help=None, trace=False):
   """Turn the internal argument record pp into an inarg record"""
   # if trace: display(pp,'.pp2inarg() input pp')
   localscope = pp[CTRL_record]['localscope']
   if pp.has_key('_getdefaults'): pp.__delitem__('_getdefaults')

   # Make the external inarg record:
   inarg = dict()
   inarg[localscope] = pp
   if trace: display(inarg,'inarg <- .pp2inarg(pp)')
   return inarg

   

#----------------------------------------------------------------------------

def attach(rr=None, inarg=None, recurse=False, level=0, trace=False):
   """Attach the inarg (or pp?) to an appropiately named field of record rr"""

   s0 = '** JEN_inarg.attach(): '

   if not isinstance(inarg, dict):
      WARNING(rr,s0+'inarg not a record, but: '+str(type(inarg)))
      return False 
   # Make sure that the composite (rr) is a record:
   if not isinstance(rr, dict): rr = dict()

   if False:
      trace = True
      if trace: display(rr,'JEN_inarg.attach(): input rr', full=True)
      if trace: display(inarg,'JEN_inarg.attach(): input inarg', full=True)

   # The inarg record should contain the name[+qualifier(s)] of 'its' function: 
   lscope = localscope(inarg)

   # Check whether rr already has this inarg:
   if rr.has_key(lscope):
      # NB: This happens with nested functions all the time, so assume OK
      #     (it is the equivalent of .setdefault(key,value), where key exists already)
      # MESSAGE(rr, s0+'duplicate localscope: '+lscope)
      return rr                                  # just return input rr

   # Recurse until rr has another field with the same barescope....
   if recurse:
      bs = barescope(inarg) 
      if not rr.has_key(bs):
         for key in rr.keys():
            if not isinstance(rr[key], dict):
               pass
            else:
               attach(rr[key], inarg, recurse=recurse, level=level+1, trace=trace)

   # OK, attach to rr:
   qq = deepcopy(inarg[lscope])               # use a copy, just in case
   _replace_reference(qq, trace=trace)        # replace any referenced values        
   rr[lscope] = qq                            # attach to rr
   MESSAGE(rr, s0+'attached: '+lscope)
   order(rr, append=lscope)                   # Update the order-field of the CTRL_record:
   if trace: display(rr,'rr <- JEN_inarg.attach()', full=True)
   return rr

#----------------------------------------------------------------------------

def order(pp=None, append=None, trace=False):
   """Get/append the order of the fields of argument record pp"""
   order = CTRL(pp, 'order')
   if append:
      order.append(append)                
      order = CTRL(pp, 'order', order)
   return order


#----------------------------------------------------------------------------

def nest(pp=None, inarg=None, trace=False):
   """Attach a nested inarg to internal argument record pp"""
   # Make sure that the CTRL record of inarg has a 'nested' field....(?)
   CTRL(inarg,'nested',True, trace=trace)
   return attach(pp, inarg=inarg, trace=trace)




#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
# Function(s) related to result-records: This an optional service that may be
# used inside a function body, to construct a somewhat organised record with
# input arguments (pp), intermediate results, and final result. It helps to
# display the result, and check for errors.
# In the future, it might be used to chain functions automaticaly....
#----------------------------------------------------------------------------

def result(rr=None, pp=None, attach=None, trace=True):
   """Attach things to the result record (rr)"""
   if not isinstance(rr, dict):
      rr = dict()

   # Attach the internal argument record (pp):
   # NB: This should be done first: rr = result(pp=pp)
   if isinstance(pp, dict):
      key = localscope(pp)

      # Make sure that rr has a JEN_inarg_CTRL record
      # NB: This allows the use of .ERROR(), .is_OK() etc
      _ensure_CTRL_record(rr, key)

      # Attach:
      rr['inarg(pp) for function: '+key] = pp

   # Attach a sub-result (anything) to rr:
   if isinstance(attach, dict):
      key = localscope(attach)
      if not isinstance(key, str): key='?localscope?'
      rr['result of function: '+key] = attach

   if trace:
      lscope = localscope(rr)
      name = 'result of function: '+lscope
      display(rr, 'JEN_inarg.result()', name=name, full=True)
   return rr


#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def inarg_template (pp, **kwargs):
   """Template/example for inarg_xxx() functions (see e.g. MG_JEN_Cohset.py)"""
   JEN_inarg.inarg_common(kwargs)
   JEN_inarg.define (pp, 'xxx', '<default>',
                     slave=kwargs['slave'], hide=kwargs['hide'],
                     choice=[],
                     help='')
   return True


def inarg_common (rr, **kwargs):
   """Used in inarg_xxx() functions (see above)"""
   rr.setdefault('slave', False)     
   rr.setdefault('hide', False)
   # NB: Think about this one, and the entire inarg_common idea!!
   # rr.setdefault('setopen', False)
   # if rr['setopen']:
      # CTRL(rr,'setopen',True, trace=trace)
   for key in kwargs.keys():
      rr[key] = kwargs[key]
   return True


#----------------------------------------------------------------------------

def define(pp, key=None, default=None, slave=False,
           choice=None, editable=None, tf=None,
           mandatory_type=None, browse=None, vector=None,
           range=None, min=None, max=None,
           help=None, hide=None, mutable=None, trace=False):
   """Define a pp entry with a default value, and other info.
   This is a more able version of pp.setdefault(key,value),
   which is helpful for a specification GUI (see JEN_inargGui.py)"""

   trace = False                           # <---------
   s1 = '.define('+str(key)+'): '
   if trace: print '\n**',s1

   _ensure_CTRL_record(pp)

   # Do some basic checks:
   if not isinstance(pp, dict):
      print s1,'pp not a record, but:',type(pp) 
      return False
   elif not isinstance(key, str):
      WARNING(pp, s1+'key not a string, but: '+str(type(key)))
      return False
   elif pp.has_key(key):
      # NB: This ALWAYS happens when executing the script with an existing inarg record...
      # NB: This may happen if executed with extra arguments....
      # MESSAGE(pp, s1+'duplicate argument key in: '+str(pp.keys()))
      return False

   # Deal with some special cases:
   if isinstance(tf, bool):          # tf (TrueFalse) specified
      default = tf                   #  
      cc = [True, False]
      if choice:
         cc.extend(choice)            # append any other choices
      choice = cc
      editable = False
   
   # Make sure that choice is a list/tuple.
   if choice==None:
      choice = []
   elif not isinstance(choice, (list, tuple)):
      choice = [choice]

   # Make sure that the default value is among the choice:
   if not (default in choice):        
      choice.insert(0,default)        # prepend 

   # In 'slaved' mode, the default is the key prepended with '@@'
   # This causes the parent record(s) of the pp record to be
   # searched for field with the same name, whose value will be used.
   # See _replace_references()
   slavedmode = '@@'+key              # 
   if slave:                          # slaved mode
      default = slavedmode            #
      hide = True
      mutable = False
   if not (slavedmode in choice):
      choice.append(slavedmode)       # always....?

   # OK, make the new argument field (key):
   pp.setdefault(key, default)

   # Update the order-field of the CTRL_record:
   order(pp, append=key)

   # Put the extra info into the control record:
   # (Use a dict (rr) to drive the loop below)
   rr = dict(choice=choice, editable=editable, 
             mandatory_type=mandatory_type,
             browse=browse, mutable=mutable,
             range=range, min=min, max=max,
             hide=hide, vector=vector, help=help)
   s2 = '- CTRL_record:'
   for field in rr.keys():
      if trace: print s2,field,' (',rr[field],'):',
      if not rr[field]==None:
         pp[CTRL_record].setdefault(field, {})
         pp[CTRL_record][field][key] = rr[field]
         if trace: print '->',rr[field]
      elif trace:
         print
   if trace: print
   return True


#********************************************************************************
#********************************************************************************
#********************************************************************************
#********************************************************************************




#========================================================================
# Test functions:
#========================================================================


def test1(ns=None, object=None, **inarg):
   """A test function with inarg capability"""
   
   # Extract a bare argument record pp from inarg
   pp = inarg2pp(inarg, 'JEN_inarg::test1()', version='10jan2006', trace=True)
   
   # Specify the function arguments, with default values:
   define(pp, 'aa', 45, choice=[46,78,54,False,None], editable=False,
          help='help for aa', trace=True)
   define(pp, 'bb', -0.19, choice=[0.2,0.5,1.5], range=[-1,1],
          help='longer string for elaborate help for bb', trace=True)
   define(pp, 'list', range(4), choice=[['a','A'],[45,-34],True],
          help='multiline help \n for list', trace=True)
   define(pp, 'hide', 'the rain in spain', hide=True,
          help='multiline help for hide', trace=True)
   define(pp, 'vector', ['aa',2,None], vector=True,
          choice=['bb','ccc',['6',7,9],True],
          help='if vector, affects editing', trace=True)
   define(pp, 'slave', 'the rain in spain', slave=True,
          help='if slaved, use @@', trace=True)
   define(pp, 'file_browse', 'xxx.py', browse='*.py',
          help='open a .py file', trace=True)
   define(pp, 'empty_string', ' ', choice=[' ',''," ",""],
          help='four versions of empty strings', trace=True)

   pp.setdefault('ref_ref_aa', '@ref_aa')
   pp.setdefault('ref_aa', '@aa')

   define(pp, 'nested', True, tf=True, trace=True)
   define(pp, 'trace', False, tf=False, trace=True)

   if pp['nested']:
      # It is possible to include the default inarg records from other
      # functions that are used in the function body below:
      nest(pp, inarg=test2(_getdefaults=True, trace=pp['trace']), trace=pp['trace'])

   # .test(_getdefaults=True) -> an inarg record with default values
   if getdefaults(pp, trace=pp['trace']): return pp2inarg(pp, trace=pp['trace'])

   # Execute the function body, using pp:
   # Initialise a result record (rr) with the argument record pp
   rr = result(pp=pp)
   if pp['nested']:
      # The inarg record for test2 is part of pp (see above):
      rr = result(rr, attach=test2(inarg=pp))
   cc = CTRL(rr)
   print 'CTRL =',cc
   MESSAGE(rr, 'result MESSAGE')
   ERROR(rr, 'result ERROR')
   WARNING(rr, 'result WARNING')
   return rr


#---------------------------------------------------------------------------

def test2(**inarg):
   """Another test function"""

   pp = inarg2pp(inarg, 'JEN_inarg::test2()', version='2.45', trace=True)
   pp.setdefault('ff', 145)
   pp.setdefault('bb', -119)
   pp.setdefault('aa', 'aa_test2')
   pp.setdefault('ref_ref_aa', '@@ref_aa')
   pp.setdefault('ref_aa', '@aa')
   pp.setdefault('trace', False)
   ERROR(pp, '...error...')
   WARNING(pp, '...warning...')
   MESSAGE(pp, '...message...')
   if getdefaults(pp, trace=pp['trace']): return pp2inarg(pp, trace=pp['trace'])

   # Initialise a result record (rr) with the argument record pp
   rr = result(pp=pp)
   return rr


#========================================================================
# Helper routines:
#========================================================================

# Counter service (....)

_counters = {}

def _counter (key, increment=0, reset=False, trace=True):
    global _counters
    _counters.setdefault(key, 0)
    if reset: _counters[key] = 0
    _counters[key] += increment
    if trace: print '** JEN_inarg: _counters(',key,') =',_counters[key]
    return _counters[key]



#********************************************************************************
#******************** PART VI: Standalone test routines *************************
#********************************************************************************
#********************************************************************************

if __name__ == '__main__':
   print '\n****************\n** Local test of: JEN_inarg.py:\n'
   from Timba.Trees import JEN_record



   #---------------------------------------------------------------------------

   if 0:
      pp = dict()
      inarg_common(pp, hide=True)
      print 'pp =',pp

   if 1:
      # Test of basic inarg-operation:
      qual = '<qual>'
      qual = None
      inarg = test1(_getdefaults=True, _qual=qual, trace=True)
      if 0:
         # modify(trace=True)
         # modify(inarg, trace=True)
         modify(inarg, aa='aa', trace=True, _JEN_inarg_option=None)
         # modify(inarg, aa='aaaa', cc='cc', trace=True)
         display(inarg, 'after .modify()', full=True)
      # result = test1(_inarg=inarg, _qual=qual, bb='override', qq='ignored', nested=False)
      display(result, 'after .test1()', full=True)
      print view(inarg)
      view(inarg, 'ERROR')
      view(inarg, 'WARNING')
      for field in ['ERROR','WARNING','MESSAGE','HISTORY','XXX']:
         print '** count(',field,') ->',count(inarg, field)

   if 0:
      # Test of traditional operation of the same function:
      result = test1(aa=23, bb='override', qq='ignored', nested=False)
      display(result, 'after .test1()', full=True)
      
   if 0:
      # Test of .clone()
      inarg = test1(_getdefaults=True)
      localscope(inarg, trace=True)
      qualifier(inarg, trace=True)
      rr = clone(inarg, 'cloned', trace=True)
      localscope(rr, trace=True)
      qualifier(rr, trace=True)
      barescope(rr, trace=True)
      attach(inarg, rr, trace=True)

      
   if 0:
      # Test of .CTRL()
      inarg = test1(_getdefaults=True)
      tf = is_inarg(inarg)
      print 'is_inarg(inarg) ->',tf
      ok = is_OK(inarg)
      print 'is_OK(inarg) ->',ok

   if 0:
      # Test of ._prefix():
      for i in range(-1,4):
         s = _prefix(i)
         print '_prefix(',i,') ->',s

   if 0:
      # Test of .CTRL()
      inarg = test1(_getdefaults=True)
      cc = CTRL(inarg, trace=True)
      ERROR(inarg,'error 1', trace=True)
      cc = CTRL(inarg, 'nested', trace=True)
      cc = CTRL(inarg, 'nested', True, trace=True)
      cc = CTRL(inarg, trace=True)
      cc = CTRL(inarg, 'nested', delete=True, trace=True)
      cc = CTRL(inarg, 'nested', trace=True)
      cc = CTRL(inarg, trace=True)
      cc = CTRL(inarg, 'ERROR', trace=True)
      cc = CTRL(inarg, 'localscope', trace=True)
      cc = CTRL(inarg, 'localscope', 45, trace=True)
      print 'cc =',cc

   if 0:
      # Test of .MESSAGE():
      inarg = test1(_getdefaults=True)
      ERROR(inarg,'error 1', trace=True)
      ERROR(inarg,'error 2', clear=True, trace=True)
      ERROR(inarg,'error 3', trace=True)
      WARNING(inarg,'warning 1', trace=True)
      MESSAGE(inarg,'MESSAGE 1', trace=True)
      WARNING(inarg, clear=True, trace=True)
      ERROR(inarg, clear=True, trace=True)

   if 0:
      # Test: Combine the inarg records of multiple functions:
      inarg1 = test1(_getdefaults=True)
      inarg2 = test2(_getdefaults=True)
      inarg = attach(inarg=inarg1, trace=True)
      attach(inarg, inarg=inarg2, trace=True)
      # attach(inarg, inarg=inarg2, trace=True)
      # r1 = test1(_inarg=inarg)        # nested!
      r2 = test2(_inarg=inarg)        # ok, test2 only
      # r3 = test2(_inarg=inarg1)         # -> error

   if 0:
      # Test of 'regular' use, i.e. without inarg:
      r1 = test2(aa=6, xx=7, trace=True)

   if 0:
      # One of the few forbidden things:
      r1 = test1(inarg=False)            # error

   if 0:
      # Test of ._strip():
      rr = test1(_getdefaults=True)
      JEN_record.display_object(rr,'rr','before ._strip(rr)')
      qq = _strip(rr, CTRL_record)
      JEN_record.display_object(qq,'qq','after ._strip(rr)')
      JEN_record.display_object(rr,'rr','after ._strip(rr)')

   if 0:
      rr = dict(aa=3, bb=4)
      display(rr,'rr', full=True)
   print '\n** End of local test of: JEN_inarg.py \n*************\n'

#********************************************************************************




# JEN_parse.py
#
# Author: J.E.Noordam
#
# Short description:
#   Contains a series of text parsing functions
#
# History:
#    - 02 july2006: creation, from TDL_Expression.py
#
# Remarks:
#
# Description:
#


#***************************************************************************************
# Preamble
#***************************************************************************************

from copy import deepcopy

# Replacement for is_numeric(): if isinstance(x, NUMMERIC_TYPES):
NUMERIC_TYPES = (int, long, float, complex)


#***************************************************************************************
#***************************************************************************************


#-------------------------------------------------------------------------------
# Functions dealing with brackets:
#----------------------------------------------------------------------------

def enclose (key, brackets='{}', trace=False):
    """Make sure that the given key is enclosed by the specified brackets"""
    bopen = str(brackets[0])
    bclose = str(brackets[1])
    if not isinstance(key, str):
        return bopen+str(key)+bclose
    if not key[0]==bopen:
        return bopen+str(key)+bclose
    return key

#----------------------------------------------------------------------------

def deenclose (key, brackets='{}', trace=False):
    """Make sure that the given key is NOT enclosed by the specified brackets"""
    # trace = True
    if trace: print '** .deenclose(',key,brackets,'):'
    keyin = key
    if not isinstance(key, str): return key
    bopen = str(brackets[0])
    if not key[0]==bopen:
        if trace: print '   first bracket is not',bopen,'->',key
        return key                              # not enclosed
    bclose = str(brackets[1])
    n = len(key)
    # if n<1: return key                        # too short
    if not key[n-1]==bclose:
        if trace: print '   last bracket is not',bclose,'->',key
        return key                              # not enclosed
    level = 0
    lmax = 0
    for i in range(n):
        if key[i]==bopen:
            level += 1
            lmax = max(level,lmax)
        elif key[i]==bclose:
            level -= 1
            if level<1 and i<(n-1):
                if trace: print '   intermediate drop to level',level,i,n-1,'->',key
                return key                      # not enclosed
    # OK, enclosed: remove enclosing brackets:
    key = key[:(n-1)]
    key = key[1:]
    if trace: print '   OK: (lmax=',lmax,level,') ->',key
    return key

#----------------------------------------------------------------------------

def find_enclosed (expr, brackets='{}', trace=False):
    """Return a list of substrings that are enclosed in the specified brackets.
    e.g. expr='{A}+{B}*{A}' would produce ['A','B']"""
    if trace: print '\n** find_enclosed(',brackets,'): ',expr
    b1 = brackets[0]                            # opening bracket
    b2 = brackets[1]                            # closing bracket
    cc = []
    level = 0
    for i in range(len(expr)):
        if expr[i]==b1:
            if not level==0:                    # nested brackets should not exist...!
                return False
            else:
                level += 1
                i1 = i
        elif expr[i]==b2:
            if not level==1:                    # wrong order....
                return False
            else:
                level -= 1
                substring = expr[i1:(i+1)]
                substring = deenclose(substring, brackets)
                if not substring in cc:
                    cc.append(substring)
                    if trace: print '-',i,level,cc
    # Some checks:
    if not level==0:
        return False
    if trace: print '   -> (',len(cc),level,'):',cc
    return cc


#----------------------------------------------------------------------------
# Split into top-level additive (+/-) terms:
#----------------------------------------------------------------------------

def find_terms (expr, level=0, trace=False):
    """Find the additive (+/-) terms of the given mathematical expression (string),
    i.e. the top-level subexpressions separated by plus and minus signs.
    Return a record with two lists: pos and neg."""

    # trace = True
    if trace: print '\n** find_terms(): ',expr

    rr = dict(pos=[],neg=[])                     # initialise output record
    nest = 0
    i1 = 0
    ncpt = 0
    n2 = 0
    expr = deenclose(expr, '()', trace=False)    # remove enclosing brackets
    nchar = len(expr)
    key = 'pos'
    for i in range(len(expr)):
        last = (i==(nchar-1))                    # True if last char
        # if trace: print nest,nest*'..',i,ncpt,n2,last,':',expr[i]
        if last:
            term = expr[i1:(i+1)]
            append_term (rr, term, key, n2, i, nest, trace=trace)
            if expr[i]==')': nest -= 1           # closing bracket
        elif expr[i]=='(':                       # opening bracket
            nest += 1
        elif expr[i]==')':                       # closing bracket
            nest -= 1
        elif nest>0:                             # nested
            if level==0:
                # Ignore, but count the higher-nested () terms.
                # This is for dealing with top-level terms that are
                # enclosed in brackets (), taking signs into account.
                if expr[i] in ['+','-']: n2 += 1
        elif expr[i] in ['+','-']:               # end of an un-nested term
            if ncpt>0:                           # some chars in term
                term = expr[i1:i]
                append_term (rr, term, key, n2, i, nest, trace=trace)
            i1 = i+1                             # first char of new term
            ncpt = 0                             # term char counter
            n2 = 0
            key = 'pos'                          # additive term
            if expr[i]=='-': key = 'neg'         # subtractive term              
        ncpt += 1                                # increment term char counter

    # Some checks:
    if not nest==0:                             # bracket imbalance
        print '\n** find_terms() Error: bracket imbalance, nest =',nest
        print 'expr =',expr
        print '\n'
        return False
    if trace: print '   -> (',nest,'):',rr
    return rr

#...............................................................................

def append_term (rr, term, key, n2, i, nest, trace=False):
    """Helper function for .find_terms()"""
    if n2>0:                             # term contains +/-
        rr1 = find_terms(term, level=1, trace=False)
        # rr1 = dict(pos=[], neg=[])
        if key=='pos':
            rr['pos'].extend(rr1['pos']) # 
            rr['neg'].extend(rr1['neg']) # 
        else:
            rr['neg'].extend(rr1['pos']) # 
            rr['pos'].extend(rr1['neg']) # 
            if trace: print '-',i,nest,key,n2,' rr1 =',rr1
    else:
        term = deenclose(term, '()', trace=False)
        rr[key].append(term)
        if trace: print '-',i,nest,key,'term =',term
    return True



#----------------------------------------------------------------------------
# Split into top-level additive (+/-) factors:
#----------------------------------------------------------------------------

def find_factors (expr, level=0, trace=False):
    """Find the additive (*/^) factors of the given mathematical expression (string),
    i.e. the top-level subexpressions separated by plus and minus signs.
    Return a record with two lists: pos and neg."""

    # trace = True
    if trace: print '\n** find_factors(): ',expr

    rr = dict(mult=[],div=[])                    # initialise output record
    nest = 0
    i1 = 0
    ncpt = 0
    n2 = 0
    expr = deenclose(expr, '()', trace=False)    # remove enclosing brackets
    nchar = len(expr)
    key = 'mult'
    for i in range(len(expr)):
        last = (i==(nchar-1))                    # True if last char
        # if trace: print nest,nest*'..',i,ncpt,n2,last,':',expr[i]
        if last:
            factor = expr[i1:(i+1)]
            append_factor (rr, factor, key, n2, i, nest, trace=trace)
            if expr[i]==')': nest -= 1           # closing bracket
        elif expr[i]=='(':                       # opening bracket
            nest += 1
        elif expr[i]==')':                       # closing bracket
            nest -= 1
        elif nest>0:                             # nested
            if level==0:
                # Ignore, but count the higher-nested () factors.
                # This is for dealing with top-level factors that are
                # enclosed in brackets (), taking signs into account.
                if expr[i] in ['*','/']: n2 += 1
        elif expr[i] in ['*','/']:               # end of an un-nested factor
            if ncpt>0:                           # some chars in factor
                factor = expr[i1:i]
                append_factor (rr, factor, key, n2, i, nest, trace=trace)
            i1 = i+1                             # first char of new factor
            ncpt = 0                             # factor char counter
            n2 = 0
            key = 'mult'                         # multiplicative factor
            if expr[i]=='/': key = 'div'         # divider              
        ncpt += 1                                # increment factor char counter

    # Some checks:
    if not nest==0:                             # bracket imbalance
        print '\n** find_factors() Error: bracket imbalance, nest =',nest
        print 'expr =',expr
        print '\n'
        return False
    if trace: print '   -> (',nest,'):',rr
    return rr

#...............................................................................

def append_factor (rr, factor, key, n2, i, nest, trace=False):
    """Helper function for .find_factors()"""
    if n2>0:                             # factor contains +/-
        rr1 = find_factors(factor, level=1, trace=False)
        if key=='mult':
            rr['mult'].extend(rr1['mult']) # 
            rr['div'].extend(rr1['div'])  # 
        else:
            rr['div'].extend(rr1['mult']) # 
            rr['mult'].extend(rr1['div']) # 
            if trace: print '-',i,nest,key,n2,' rr1 =',rr1
    else:
        factor = deenclose(factor, '()', trace=False)
        rr[key].append(factor)
        if trace: print '-',i,nest,key,'factor =',factor
    return True


#-----------------------------------------------------------------------
# Find unary functions, e.g. cos()
#-----------------------------------------------------------------------

def find_unary (expr, trace=False):
    """Find unary functions (e.g. cos(...)) in the given expr string.
    Return them as fields (lists) in a record: rr['cos'] = ['a+b', 'c']"""
    if trace: print '\n** .find_unary(',expr,'):'
    keys = ['cos','sin','tan']
    keys.extend(['log','exp'])
    rr = dict()
    n = len(expr)
    for key in keys:
        k2 = 0
        count = 0
        while k2<n:
            count += 1
            if count>5: break
            k1 = k2 + expr[k2:].find(key+'(')          # e.g. look for 'cos('
            if k1<k2:                                  # not found
                k2 = n
            else:
                nest = 0
                k1 += len(key)
                for k2 in range(k1,n):
                    if expr[k2]=='(':
                        nest += 1
                    elif expr[k2]==')':
                        nest -= 1
                        if nest==0:
                            rr.setdefault(key,[])
                            argstr = expr[(k1+1):k2]   # argument string
                            if not rr[key].__contains__(argstr):
                                rr[key].append(argstr)
                                if trace: print '-',key,':',rr[key]
                            break
                if not nest==0:
                    print 'ERROR: bracket mismatch in:',expr[k1:]
    return rr
    


#========================================================================
# Test routine:
#========================================================================


if __name__ == '__main__':
    print '\n*******************\n** Local test of: JEN_parse.py:\n'

    if 0:
        for x in [3,3.4,12345678907777777777777,'a',3+7j]:
            tf = isinstance(x, NUMERIC_TYPES)
            print '- isinstance(',x,type(x),', NUMERIC_TYPES) ->',tf

    if 1:
        find_unary('cos(a+b)', trace=True)
        find_unary('cos(a+b)+sin(b)*cos(a+c)', trace=True)
        find_unary('cos(a+b*sin(qq*exp()))', trace=True)

    if 0:
        find_terms('{r}*{b}', trace=True)
        find_terms('{r}+{BA}*[t]+{A[1,2]}-{xxx}', trace=True)
        find_terms('({r}+{BA}*[t]+{A[1,2]}-{xxx})', trace=True)
        find_terms('{r}+({BA}*[t]+{A[1,2]})-{xxx}', trace=True)
        find_terms('{r}-({BA}*[t]+{A[1,2]})-{xxx}', trace=True)
        find_terms('{r}-({BA}*[t]-{A[1,2]})-{xxx}', trace=True)
        find_terms('{r}+(-{BA}*[t]+{A[1,2]})-{xxx}', trace=True)
        find_terms('{r}-(-{BA}*[t]+{A[1,2]})-{xxx}', trace=True)
        find_terms('-{r}-(-{BA}*[t]+{A[1,2]})-{xxx}-5', trace=True)
        find_terms('(cos(-{BA}*[t]))', trace=True)
        find_terms('{r}-(cos(-{BA}*[t])+{A[1,2]})-{xxx}', trace=True)

    if 0:
        find_factors('{r}*{b}', trace=True)
        find_factors('{r}*{BA}*[t]*{A[1,2]}/{xxx}', trace=True)
        find_factors('({r}*{BA}*[t]*{A[1,2]}/{xxx})', trace=True)
        find_factors('{r}*({BA}*[t]*{A[1,2]})/{xxx}', trace=True)
        find_factors('{r}/({BA}*[t]*{A[1,2]})/{xxx}', trace=True)
        find_factors('{r}/({BA}*[t]/{A[1,2]})/{xxx}', trace=True)
        find_factors('{r}*(-{BA}*[t]*{A[1,2]})/{xxx}', trace=True)
        find_factors('{r}/(-{BA}*[t]*{A[1,2]})/{xxx}', trace=True)
        find_factors('-{r}/(-{BA}*[t]*{A[1,2]})/{xxx}/5', trace=True)
        find_factors('(cos(-{BA}*[t]))', trace=True)
        find_factors('{r}/(cos(-{BA}*[t])*{A[1,2]})/{xxx}', trace=True)

    if 0:
        deenclose('{aa_bb}', trace=True)
        deenclose('{aa}+{bb}', trace=True)
        deenclose('{{aa}+{bb}}', trace=True)

    if 0:
        find_enclosed('{A}+{BA}*[t]+{A}', brackets='{}', trace=True)
        find_enclosed('{A}+{BA}*[t]', brackets='[]', trace=True)

    if 0:
        ss = find_enclosed('{A[0,1]}', brackets='[]', trace=True)
        ss = find_enclosed('A', brackets='[]', trace=True)
        ss = find_enclosed('A[5]', brackets='[]', trace=True)
        print ss,'->',ss[0].split(',')
        
    print '\n*******************\n** End of local test of: JEN_Expression.py:\n'




#============================================================================================
# Remarks:
#
#============================================================================================

    
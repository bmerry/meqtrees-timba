//  CountedRef.h: type-specific counted reference class
//
//  Copyright (C) 2002
//  ASTRON (Netherlands Foundation for Research in Astronomy)
//  P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
//
//  This program is free software; you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation; either version 2 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//
//  $Id$

#ifndef DMI_CountedRef_h
#define DMI_CountedRef_h 1

#include <DMI/Common.h>
#include <DMI/DMI.h>
#include <DMI/CountedRefBase.h>
#include <DMI/Loki/TypeManip.h>
#include <DMI/HIID.h>

using Loki::Type2Type;
using Loki::Int2Type;

// forward declaration of NestableContainer
class NestableContainer;

//##ModelId=3BEFECFF0287
//##Documentation
//## This is a type-specific interface to the counted reference
//## mechanism, providing most of the same functions as CountedRefBase,
//## but tailored for type T.  Refer to CountedRefBase for all details.
template <class T>
class CountedRef : private CountedRefBase
{
  public:
      // Helper template determines if ref can be converted to a
      // CountedRef<U> ref. Incompatible types will generate a compile- or
      // run-time error. Compatible types return a CountedRefBase &.
      template <class U,class UisSuperclass>
      const CountedRefBase & compatible (Type2Type<U>,UisSuperclass) const
      {
        // a ref to a subclass can always be converted to 
        // a superclass ref (this also covers the case of From==To) 
        return *this;
      }
      // Partial specialization: a ref to a superclass can only be converted to a 
      // subclass ref if it currently points to an object of that subclass
      template <class U>
      const CountedRefBase & compatible (Type2Type<U>,Int2Type<false>) const
      {
        STATIC_CHECK( SUPERSUBCLASS(T,U),Incompatible_CountedRef_types );
        FailWhen(target && !dynamic_cast<const U*>(target),
                  "incompatible CountedRef types");
        return *this;
      }
      
      // finally, implement the real compatible() func
      template <class U>
      const CountedRefBase & compatible (Type2Type<U>) const
      { 
        return compatible(Type2Type<U>(),Int2Type<SUPERSUBCLASS(U,T)>());
      }
      
  public:
    //##ModelId=3E9BD91401F0
      typedef CountedRef<T> Xfer;
    //##ModelId=3E9BD9140239
      typedef CountedRef<T> Copy;
      
      //##ModelId=3BF9396D01A7
      CountedRef()
      {}

      //##ModelId=3BF93C020247
      //## copy constructor is templated to allow conversion between
      //## refs to sub/superclasses
      template<class U>
      CountedRef(const CountedRef<U> &right)
        : CountedRefBase(right.compatible(Type2Type<T>()))
      {}
      //##ModelId=3BF93D620128
      //##Documentation
      //## Generic copy constructor -- see same method in CountedRefBase.
      //## Copy constructor is templated to allow conversion between
      //## refs to sub/superclasses
      template<class U>
      CountedRef (const CountedRef<U>& other, int flags, int depth = -1)
        : CountedRefBase(other.compatible(Type2Type<T>()),flags,depth)
      {
      }

      //##ModelId=3BF93C020247
      explicit CountedRef (T& targ, int flags = 0);
      //##ModelId=3BF93D620128
      explicit CountedRef (const T& targ, int flags = 0);
      //##ModelId=3BF93F8D0054
      explicit CountedRef (T* targ, int flags = 0);
      //##ModelId=3BF93F9702C5
      explicit CountedRef (const T* targ, int flags = 0);

    //##ModelId=3DB934580238
      //## Assignment is templated to allow conversion between
      //## refs to sub/superclasses
      template<class U>
      CountedRef<T> & operator= (const CountedRef<U> &right)
      {
        CountedRefBase::operator = (right.compatible(Type2Type<T>()));
        return *this;
      }
    //##ModelId=3DB934590080
      template<class U>
      bool operator == (const CountedRef<U> &right) const
      { return target != 0 && target == right.target; }

    //##ModelId=3DB934590329
      template<class U>
      bool operator != (const CountedRef<U> &right) const
      { return !(*this == right); }


      //##ModelId=3C8F61C80241
      const T* deref_p () const;

      //##ModelId=3BEFED870110
      //##Documentation
      //## Dereferences to const target.
      const T& deref () const;

      //##ModelId=3BF55FDC0049
      //##Documentation
      //## Overloaded deref op, so that ref->method() can be used to call
      //## target's const methods.
      const T* operator -> () const;

      //##ModelId=3C5FBE030173
      const T& operator * () const;

      //##ModelId=3C8F61D10199
      T* dewr_p () const;

      //##ModelId=3BEFF73602B0
      //##Documentation
      //## Dereferences to non-const object.
      T& dewr () const;

      //##ModelId=3C0F806901C1
      //##Documentation
      //## Dereferences to non-const object. Use e.g. ref().method() to call
      //## target's non-const methods.
      T& operator () () const;

      //##ModelId=3C0F808100DF
      //##Documentation
      //## Conversion operators to T& and T* do. implicit dereferencing.
      operator const T& () const;

      //##ModelId=3C0F80A50055
      operator const T* () const;

      //##ModelId=3C0F80B501D4
      operator T& () const;

      //##ModelId=3C0F80C0020C
      operator T* () const;

      //##ModelId=3BF93A170291
      //##Documentation
      //## Copies ref -- see CountedRefBase::copy().
      //## Templated, so as to allow conversion between
      //## refs to sub/superclasses
      template<class U>
      CountedRef<U> copy (int flags,int depth,U*) const
      {
        return CountedRef<U>(*this,flags|DMI::COPYREF,depth);
      }
      
    //##ModelId=3BF93A170291
      CountedRef<T> copy (int flags = 0,int depth = -1) const
      { 
        return CountedRef<T>(*this,flags|DMI::COPYREF,depth);
      }
      
      template<class U>
      CountedRef<U> copy (U*) const
      {
        return CountedRef<U>(*this,DMI::COPYREF,-1);
      }

      //##ModelId=3C1F2DB802D2
      //## Templated, so as to allow conversion between
      //## refs to sub/superclasses
      template<class U>
      CountedRef<T> & copy (const CountedRef<U>& other, int flags = 0, int depth = -1)
      {
        CountedRefBase::copy(other.compatible(Type2Type<T>()),flags,depth);
        return *this;
      }

      //##ModelId=3C1F2DD30353
      //## Templated, so as to allow conversion between
      //## refs to sub/superclasses
      template<class U>
      CountedRef<T> & xfer (const CountedRef<U>& other)
      {
        CountedRefBase::xfer(other.compatible(Type2Type<T>()));
        return *this;
      }

      //##ModelId=3C17A06901DC
      //##Documentation
      //## Privatizes a ref -- see CountedRefBase::privatize().
      CountedRef<T>& privatize (int flags = 0, int depth = 0);

      //##ModelId=3C187F270346
      //##Documentation
      //## Locks ref -- see CountedRefBase::lock().
      CountedRef<T>& lock ();

      //##ModelId=3C187F2E0291
      //##Documentation
      //## Unlocks ref -- see CountedRefBase::unlock().
      CountedRef<T>& unlock ();

      //##ModelId=3C501A15015C
      CountedRef<T>& persist ();

      //##ModelId=3C501A1C01FD
      CountedRef<T>& unpersist ();

      //##ModelId=3C1897A5032E
      //##Documentation
      //## Changes ref properties -- see CountedRefBase::change().
      CountedRef<T>& change (int flags);

      //##ModelId=3C1897B50178
      //##Documentation
      //## Makes exclusive writer -- see  CountedRefBase::setExclusiveWrite()
      CountedRef<T>& setExclusiveWrite ();

      //##ModelId=3BFA4DF4027D
      //##Documentation
      //## Various methods to attach to target object. See CountedRefBase::
      //## attach(). Const target forces readonly ref.
      CountedRef<T> & attach (T* targ, int flags = 0)
      { CountedRefBase::attach(targ,flags); return *this; }

      //##ModelId=3BFA4E070216
      CountedRef<T> & attach (const T* targ, int flags = 0)
      { CountedRefBase::attach(targ,flags); return *this; }
      
      //##ModelId=3C179D9E027E
      CountedRef<T> & attach (T& targ, int flags = 0)
      { return attach(&targ,flags); } 

      //##ModelId=3C179DA9016B
      CountedRef<T> & attach (const T& targ, int flags = 0)
      { return attach(&targ,flags); } 

      //##ModelId=3CBEE39B0011
      //##Documentation
      //## <<= on const target ptr is alias for attach as readonly, anonymous
      const T& operator <<= (const T* targ)
      {
        attach(targ,DMI::ANON|DMI::READONLY);
        return *targ;
      }
      //##ModelId=3CBEE3AC0105
      //##Documentation
      //## <<= on target ptr is alias for attach as r/w, anonymous
      T& operator <<= (T* targ)
      {
        attach(targ,DMI::ANON|DMI::WRITE);
        return *targ;
      }
      
      //##ModelId=3E01B1AB0345
      //##Documentation
      //## <<= on other ref is alias for xfer
      template<class U>
      CountedRef<T> & operator <<= (const CountedRef<U> &other)
      {
        return xfer(other);
      }

    // Additional Public Declarations
      // Constructor for implicitly allocating a new anonymous target.
      // Flags must contain DMI::ANON, else exception is thrown.
      // T must have a default constructor.
      // Use, e.g.: CountedRef<T> ref(DMI::ANONWR);
    //##ModelId=3DB934560267
      explicit CountedRef (int flags); 
      
      // make public some methods of CountedRefBase which would otherwise
      // be hidden by private inheritance
    //##ModelId=3DB934500207
      CountedRefBase::valid;
    //##ModelId=3DB9345003DE
      CountedRefBase::detach;
    //##ModelId=3DB934510135
      CountedRefBase::isLocked;
    //##ModelId=3DB934510276
      CountedRefBase::isWritable;
    //##ModelId=3DB934520105
      CountedRefBase::isAnonObject;
    //##ModelId=3DB934520250
      CountedRefBase::hasOtherWriters;
    //##ModelId=3DB934520390
      CountedRefBase::verify; 
    //##ModelId=3E01B0F70100
      CountedRefBase::print;
    //##ModelId=3DB934530111
      CountedRefBase::debug;
    //##ModelId=3DB93453025B
      CountedRefBase::sdebug;
      
      // Add methods for in-place conversion between ref types.
      // Use with care! Since it returns itself by reference, calling this 
      // method on a temporary object can leave you with an invalid reference.
      // The dummy U* argument is there to help template matching
      template<class U>
      CountedRef<U> & ref_cast (Type2Type<U>)
      { 
        compatible(Type2Type<U>());
        return *reinterpret_cast<CountedRef<U>*>(this); 
      }
      
      template<class U>
      const CountedRef<U> & ref_cast (Type2Type<U>) const
      {
        compatible(Type2Type<U>());
        return *reinterpret_cast<const CountedRef<U>*>(this); 
      }
      // versions using a dummy U* argument
      template<class U>
      CountedRef<U> & ref_cast (U* =0) 
      { return ref_cast(Type2Type<U>()); }
      template<class U>
      const CountedRef<U> & ref_cast (U* =0) const
      { return ref_cast(Type2Type<U>()); }
      
      // Add operator [] for implicit indexing into contents.
      // So far, this is only implemented in NestableContainer
    //##ModelId=4017F61F039E
      typename T::OpSubscriptReturnType operator [] (const HIID &id) const
      { return T::apply_subscript(ref_cast<typename T::OpSubscriptRefType>(),id); }
      
    //##ModelId=4017F6200027
      typename T::OpSubscriptReturnType operator [] (const HIID &id)
      { return T::apply_subscript(ref_cast<typename T::OpSubscriptRefType>(),id); }
      
#define declareSubscriptAliases(RetType,constness) \
          RetType operator [] (int id1) constness  \
           { return (*this)[HIID(id1)]; }  \
          RetType operator [] (AtomicID id1) constness  \
           { return (*this)[HIID(id1)]; }  \
          RetType operator [] (const string &id1) constness  \
           { return (*this)[HIID(id1)]; }  \
          RetType operator [] (const char *id1) constness \
           { return (*this)[HIID(id1)]; }  

#define declareParenthesesAliases(RetType,constness) \
      RetType operator () (AtomicID id1) constness \
      { return (*this)[id1]; }  \
      RetType operator () (AtomicID id1,AtomicID id2) constness \
      { return (*this)[id1|id2]; }  \
      RetType operator () (AtomicID id1,AtomicID id2,AtomicID id3) constness \
      { return (*this)[id1|id2|id3]; }  \
      RetType operator () (AtomicID id1,AtomicID id2,AtomicID id3,AtomicID id4) constness \
      { return (*this)[id1|id2|id3|id4]; }  
          
    //##ModelId=4017F6200081
      declareSubscriptAliases(typename T::OpSubscriptReturnType,const);
    //##ModelId=4017F6200104
      declareSubscriptAliases(typename T::OpSubscriptReturnType,);
      
  protected:
    // Additional Protected Declarations
    //##ModelId=3DB934540014
      CountedRefBase::target;
  
};

//##ModelId=3BF93C020247
template <class T>
inline CountedRef<T>::CountedRef (T& targ, int flags)
  : CountedRefBase()
{
  attach(&targ,flags);
}

//##ModelId=3BF93D620128
template <class T>
inline CountedRef<T>::CountedRef (const T& targ, int flags)
  : CountedRefBase()
{
  attach(&targ,flags|DMI::READONLY);
}

//##ModelId=3BF93F8D0054
template <class T>
inline CountedRef<T>::CountedRef (T* targ, int flags)
  : CountedRefBase()
{
  if( !flags&DMI::EXTERNAL )
    flags |= DMI::ANON;
  attach(targ,flags);
}

//##ModelId=3BF93F9702C5
template <class T>
inline CountedRef<T>::CountedRef (const T* targ, int flags)
  : CountedRefBase()
{
  if( !flags&DMI::EXTERNAL )
    flags |= DMI::ANON;
  attach(targ,flags|DMI::READONLY);
}

//##ModelId=3C8F61C80241
template <class T>
inline const T* CountedRef<T>::deref_p () const
{
  return static_cast<const T*>( getTarget() );
}

//##ModelId=3BEFED870110
template <class T>
inline const T& CountedRef<T>::deref () const
{
  return *deref_p();
}

template <class T>
inline const T* CountedRef<T>::operator -> () const
{
  return deref_p();
}

//##ModelId=3C5FBE030173
template <class T>
inline const T& CountedRef<T>::operator * () const
{
  return deref();
}

//##ModelId=3C8F61D10199
template <class T>
inline T* CountedRef<T>::dewr_p () const
{
  return static_cast<T*>(getTargetWr());
}

//##ModelId=3BEFF73602B0
template <class T>
inline T& CountedRef<T>::dewr () const
{
  return *dewr_p();
}

//##ModelId=3C0F806901C1
template <class T>
inline T& CountedRef<T>::operator () () const
{
  return dewr();
}

//##ModelId=3C0F808100DF
template <class T>
inline CountedRef<T>::operator const T& () const
{
  return deref();
}

//##ModelId=3C0F80A50055
template <class T>
inline CountedRef<T>::operator const T* () const
{
  return deref_p();
}

//##ModelId=3C0F80B501D4
template <class T>
inline CountedRef<T>::operator T& () const
{
  return dewr();
}

//##ModelId=3C0F80C0020C
template <class T>
inline CountedRef<T>::operator T* () const
{
  return dewr_p();
}

//##ModelId=3C17A06901DC
template <class T>
inline CountedRef<T>& CountedRef<T>::privatize (int flags, int depth)
{
// This simply defers to the base class Tclone(). It is provided here
// so that specifc types may implement specific kind of cloning.
  CountedRefBase::privatize(flags,depth);
  return *this;
}

//##ModelId=3C187F270346
template <class T>
inline CountedRef<T>& CountedRef<T>::lock ()
{
  CountedRefBase::lock();
  return *this;
}

//##ModelId=3C187F2E0291
template <class T>
inline CountedRef<T>& CountedRef<T>::unlock ()
{
  CountedRefBase::unlock();
  return *this;
}

//##ModelId=3C501A15015C
template <class T>
inline CountedRef<T>& CountedRef<T>::persist ()
{
  CountedRefBase::persist();
  return *this;
}

//##ModelId=3C501A1C01FD
template <class T>
inline CountedRef<T>& CountedRef<T>::unpersist ()
{
  CountedRefBase::unpersist();
  return *this;
}

//##ModelId=3C1897A5032E
template <class T>
inline CountedRef<T>& CountedRef<T>::change (int flags)
{
  CountedRefBase::change(flags);
  return *this;
}

//##ModelId=3C1897B50178
template <class T>
inline CountedRef<T>& CountedRef<T>::setExclusiveWrite ()
{
  CountedRefBase::setExclusiveWrite();
  return *this;
}

//##ModelId=3DB934560267
template <class T>
inline CountedRef<T>::CountedRef (int flags)
  : CountedRefBase()
{
  FailWhen(!flags&DMI::ANON,"DMI::ANON must be specified in constructor");
  attach(new T,flags);
}

// Template for copying STL containers of CountedRefs. Uses iterators
// to copy() every ref in the source container, passing the supplied flags
// to ref.copy(). For this implementation to work, destination
// container must support the explicit resize operation.
template<class SrcCont,class DestCont>
void copyRefContainer (DestCont &dest,const SrcCont &src,int flags=DMI::PRESERVE_RW,int depth=-1)
{
  dest.resize(src.size());
  typename SrcCont::const_iterator si = src.begin();
  typename DestCont::iterator di = dest.begin();
  for( ; si != src.end(); si++,di++ )
    di->copy(*si,flags,depth);
}

// The DefineRefTypes macro generates typedefs for refs to specific types.
// E.g.: DefineRefType(SmartBlock,BlockRef) will define
//    BlockRef (as CountedRef<SmartBlock>), 
#define DefineRefTypes(type,reftype) typedef CountedRef<type> reftype; 


#endif

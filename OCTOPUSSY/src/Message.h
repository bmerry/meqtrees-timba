//
//% $Id$ 
//
//
// Copyright (C) 2002-2007
// The MeqTree Foundation & 
// ASTRON (Netherlands Foundation for Research in Astronomy)
// P.O.Box 2, 7990 AA Dwingeloo, The Netherlands
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>,
// or write to the Free Software Foundation, Inc., 
// 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//

#ifndef OCTOPUSSY_Message_h
#define OCTOPUSSY_Message_h 1

#include <TimBase/CheckConfig.h>
#include <DMI/SmartBlock.h>
#include <DMI/HIID.h>
#include <DMI/Record.h>
#include <OCTOPUSSY/OctopussyDebugContext.h>
#include <OCTOPUSSY/MsgAddress.h>
#include <OCTOPUSSY/TID-OCTOPUSSY.h>
#include <OCTOPUSSY/AID-OCTOPUSSY.h>
#include <OCTOPUSSY/LatencyVector.h>

// if not in debug mode, disable latency stats
#if !LOFAR_DEBUG
  #undef ENABLE_LATENCY_STATS
#endif

namespace Octopussy
{
using namespace DMI;

#ifdef ENABLE_LATENCY_STATS
  CHECK_CONFIG(Message,LatencyStats,yes);
#else
  CHECK_CONFIG(Message,LatencyStats,no);
#endif

#pragma types #Octopussy::Message
#pragma aid Index Text

class WPQueue;

//##ModelId=3C7B6A2D01F0

class Message : public DMI::BObj
{
  public:
      // some predefined priority levels
      // a priority<0 is considered "none"
    //##ModelId=3DB9369D01B2
      static const int PRI_LOWEST  = 0,
                       PRI_LOWER   = 0x10,
                       PRI_LOW     = 0x20,
                       PRI_NORMAL  = 0x100,
                       PRI_HIGH    = 0x200,
                       PRI_HIGHER  = 0x400,
                       PRI_EVENT   = 0x800;
                       
      // message delivery/subscription scope
    //##ModelId=3DB936510032
      typedef enum {
           GLOBAL        = 2,
           HOST          = 1,
           PROCESS       = 0,
           LOCAL         = 0
      } MessageScope;
           
      // message processing results (returned by WPInterface::receive(), etc.)
    //##ModelId=3DB936510104
      typedef enum {  
        ACCEPT   = 0, // message processed, OK to remove from queue
        HOLD     = 1, // hold the message (and block queue) until something else happens
        REQUEUE  = 2, // requeue the message and try again
        CANCEL   = 3  // for input()/timeout()/signal(), cancel the input or timeout
      } MessageResults;
           
    //##ModelId=3DB9365101AF
      typedef CountedRef<Message> Ref;

    //##ModelId=3C8CB2CE00DC
      Message();

    //##ModelId=3C7B9C490384
      Message(const Message &right,int flags=0,int depth=0);

      //##ModelId=3C7B9D0A01FB
      explicit Message (const HIID &id1, int pri = PRI_NORMAL);

      // constructors with various payloads
      //##ModelId=3C7B9D3B02C3
      Message (const HIID &id1, DMI::BObj *pload, int flags = 0, int pri = PRI_NORMAL);
      Message (const HIID &id1, const DMI::BObj *pload, int flags = 0, int pri = PRI_NORMAL);
      //##ModelId=3C7B9D59014A
      Message (const HIID &id1, const ObjRef &pload, int flags = 0, int pri = PRI_NORMAL);
      //##ModelId=3C7BB3BD0266
      Message (const HIID &id1, SmartBlock *bl, int flags = 0, int pri = PRI_NORMAL);
      Message (const HIID &id1, const SmartBlock *bl, int flags = 0, int pri = PRI_NORMAL);;
      //##ModelId=3DB936A5029F
      Message (const HIID &id1, const BlockRef &bl, int flags = 0, int pri = PRI_NORMAL);
      //##ModelId=3DB936A7019E
      Message (const HIID &id1, const char *data, size_t sz, int pri = PRI_NORMAL);
      
    //##ModelId=3DB936A90143
      ~Message();

    //##ModelId=3DB936A901E3
      Message & operator=(const Message &right);

      //##ModelId=3C7B9DDE0137
      DMI::BObj & operator <<= (DMI::BObj *pload);
      
      DMI::Record & operator <<= (DMI::Record *pload)
      {
        operator <<= ( static_cast<DMI::BObj*>(pload) );
        return *pload;
      }

      //##ModelId=3C7B9DF20014
      Message & operator <<= (ObjRef &pload);

      //##ModelId=3C7B9E0A02AD
      SmartBlock & operator <<= (SmartBlock *bl);

      //##ModelId=3C7B9E1601CE
      Message & operator <<= (BlockRef &bl);

      //##ModelId=3C7E32BE01E0
      //##Documentation
      //## Abstract method for cloning an object. Should return pointer to new
      //## object. Flags: DMI::WRITE if writable clone is required, DMI::DEEP
      //## for deep cloning (i.e. contents of object will be cloned as well).
      virtual CountedRefTarget* clone (int flags = 0, int depth = 0) const;

      //##ModelId=3C7E32C1022B
      //##Documentation
      void cloneOther (const Message &other,int flags=0, int depth=0);

      // Define the subscript operator on messages
      // This will subscript directly into the payload
      DMI::Container::Hook operator [] (const HIID &id) const;
      // If no payload, initializes new DMI::Record
      DMI::Container::Hook operator [] (const HIID &id);
      
      declareSubscriptAliases(DMI::Container::Hook,const);
      declareSubscriptAliases(DMI::Container::Hook,);

      //##ModelId=3C7E443A016A
      void * data ();

      //##ModelId=3C7E446B02B5
      const void * data () const;

      //##ModelId=3C7E443E01B6
      size_t datasize () const;

      //##ModelId=3C960F16009B
      //##Documentation
      //## Returns the class TypeId
      virtual TypeId objectType () const;

      //##ModelId=3C960F1B0373
      //##Documentation
      //## Creates object from a set of block references. Appropriate number of
      //## references are removed from the head of the BlockSet. Returns # of
      //## refs removed.
      virtual int fromBlock (BlockSet& set);

      //##ModelId=3C960F20037A
      //##Documentation
      //## Stores an object into a set of blocks. Appropriate number of refs
      //## added to tail of BlockSet. Returns # of block refs added.
      virtual int toBlock (BlockSet &set) const;

    //##ModelId=3DB936AA02FD
      int priority () const;
    //##ModelId=3DB936AB0056
      void setPriority (int value);

    //##ModelId=3DB936AB02F5
      int state () const;
    //##ModelId=3DB936AC006B
      void setState (int value);

    //##ModelId=3DB936AC0332
      short hops () const;
    //##ModelId=3DB936AD00DB
      void setHops (short value);
    //##ModelId=3DB936BD01D9
      short addHop ();

    //##ModelId=3DB936AD03CA
      const MsgAddress& to () const;
    //##ModelId=3DB936AE015E
      void setTo (const MsgAddress& value);

    //##ModelId=3DB936AF0070
      const MsgAddress& from () const;
    //##ModelId=3DB936AF0214
      void setFrom (const MsgAddress& value);

    //##ModelId=3DB936B00161
      const HIID& id () const;
    //##ModelId=3DB936B00306
      void setId (const HIID& value);

    //##ModelId=3DB936B10360
      const ObjRef& payload () const;
    //##ModelId=3DB936BC0051
      ObjRef &     payload ();
      
      // returns type of payload object, or 0 for none
      TypeId payloadType () const;
     // This accesses the payload as a DMI::Record, or throws an exception if it isn't one
    //##ModelId=3DB936BC02B4
      const DMI::Record & record () const;
    //##ModelId=3DB936BD00A3
      DMI::Record & wrecord ();
      

    //##ModelId=3DB936B20112
      const BlockRef& block () const;
    //##ModelId=3DB936BC0192
      BlockRef &   block   ();

    //##ModelId=3DB936B202E9
      const MsgAddress& forwarder () const;
    //##ModelId=3DB936B300D8
      void setForwarder (const MsgAddress& value);

    // utility functions for constructing a message with a DMI::Record payload
    //##ModelId=3E301BB10085
      static DMI::Record & withRecord (Message::Ref &ref,const HIID &id);
    // second form initializes record with a Text field
    //##ModelId=3E301BB10140
      static DMI::Record & withRecord (Message::Ref &ref,const HIID &id,const string &text);

    //##ModelId=3DB936A10054
      int flags_; // user-defined flag field
      
#ifdef ENABLE_LATENCY_STATS
    //##ModelId=3DB958F6030D
      LatencyVector latency;
#else
      static DummyLatencyVector latency;    
#endif
      
      // This is a typical debug() method setup. The sdebug()
      // method creates a debug info string at the given level of detail.
    //##ModelId=3DB936C40273
      string sdebug ( int detail = 1,const string &prefix = "",
                const char *name = 0 ) const;
      
      ImportDebugContext(OctopussyDebugContext);

  protected:
    // Additional Protected Declarations
    //##ModelId=3E08EC000079
      BlockSet payload_set;
  private:
    // Data Members for Class Attributes

      //##ModelId=3C7B94970023
      int priority_;

      //##ModelId=3C7E33F40330
      int state_;

      //##ModelId=3CC952D7039B
      short hops_;

    // Data Members for Associations

      //##ModelId=3C7B7100015E
      MsgAddress to_;

      //##ModelId=3C7B7106029D
      MsgAddress from_;

      //##ModelId=3E08EC00008E
      HIID id_;

      //##ModelId=3DB958F60344
      ObjRef payload_;

      //##ModelId=3E08EC0000A2
      BlockRef block_;

      //##ModelId=3CC9530903D9
      MsgAddress forwarder_;

    // Additional Implementation Declarations
    //##ModelId=3DB93651024F
      class HeaderBlock : public BObj::Header
      {  
        public:
          int priority,state,flags,idsize,fromsize,tosize,latsize;
          short hops;
          bool has_block;
          TypeId payload_type;
      };
};

//##ModelId=3C7B722600DE

//##ModelId=3C7B9D0A01FB
inline Message::Message (const HIID &id1, int pri)
   : priority_(pri),state_(0),hops_(0),id_(id1)
{
}


inline DMI::Container::Hook Message::operator [] (const HIID &id) const
{
  FailWhen(!payload_.valid() || !payload_->isNestable(),"message payload is not a container" ); 
  const DMI::Container *pcont = payload_.ref_cast<DMI::Container>().deref_p();
  return (*pcont)[id];
}

inline DMI::Container::Hook Message::operator [] (const HIID &id) 
{
  if( payload_.valid() )
  { 
    FailWhen( !payload_->isNestable(),"message payload is not a container" ); 
    DMI::Container::Ref *pref = &( payload_.ref_cast<DMI::Container>() );
    return (*pref)[id];
  }
  else // init new Record as payload
  {
    DMI::Record *rec = new DMI::Record;
    payload_ <<= rec;
    return (*rec)[id];
  }
}

//##ModelId=3C7E443A016A
inline void * Message::data ()
{
  return block_.valid() ? block_().data() : 0;
}

//##ModelId=3C7E446B02B5
inline const void * Message::data () const
{
  return block_.valid() ? block_->data() : 0;
}

//##ModelId=3C7E443E01B6
inline size_t Message::datasize () const
{
  return block_.valid() ? block_->size() : 0;
}

//##ModelId=3C960F16009B
inline TypeId Message::objectType () const
{
  return TpOctopussyMessage;
}

//##ModelId=3DB936AA02FD
inline int Message::priority () const
{
  return priority_;
}

//##ModelId=3DB936AB0056
inline void Message::setPriority (int value)
{
  priority_ = value;
}

//##ModelId=3DB936AB02F5
inline int Message::state () const
{
  return state_;
}

//##ModelId=3DB936AC006B
inline void Message::setState (int value)
{
  state_ = value;
}

//##ModelId=3DB936AC0332
inline short Message::hops () const
{
  return hops_;
}

//##ModelId=3DB936AD00DB
inline void Message::setHops (short value)
{
  hops_ = value;
}

//##ModelId=3DB936AD03CA
inline const MsgAddress& Message::to () const
{
  return to_;
}

//##ModelId=3DB936AE015E
inline void Message::setTo (const MsgAddress& value)
{
  to_ = value;
}

//##ModelId=3DB936AF0070
inline const MsgAddress& Message::from () const
{
  return from_;
}

//##ModelId=3DB936AF0214
inline void Message::setFrom (const MsgAddress& value)
{
  from_ = value;
}

//##ModelId=3DB936B00161
inline const HIID& Message::id () const
{
  return id_;
}

//##ModelId=3DB936B00306
inline void Message::setId (const HIID& value)
{
  id_ = value;
}

//##ModelId=3DB936B10360
inline const ObjRef& Message::payload () const
{
  return payload_;
}

//##ModelId=3DB936B20112
inline const BlockRef& Message::block () const
{
  return block_;
}

//##ModelId=3DB936B202E9
inline const MsgAddress& Message::forwarder () const
{
  return forwarder_;
}

//##ModelId=3DB936B300D8
inline void Message::setForwarder (const MsgAddress& value)
{
  forwarder_ = value;
}

//##ModelId=3DB936BC0051
inline ObjRef& Message::payload () 
{
  return payload_;
}

//##ModelId=3DB936BC0192
inline BlockRef& Message::block () 
{
  return block_;
}

//##ModelId=3DB936BD01D9
inline short Message::addHop ()                               
{ 
  return ++hops_; 
}

inline TypeId Message::payloadType () const
{
  if( payload_.valid() )
    return payload_->objectType();
  else
    return 0;
}

//##ModelId=3DB936BC02B4
inline const DMI::Record & Message::record () const
{
  const DMI::Record *rec = dynamic_cast<const DMI::Record *>(payload_.deref_p());
  FailWhen(!rec,"payload is not a DMI::Record");
  return *rec;
}

//##ModelId=3DB936BD00A3
inline DMI::Record & Message::wrecord ()
{
  DMI::Record *rec = dynamic_cast<DMI::Record *>(payload_.dewr_p());
  FailWhen(!rec,"payload is not a DMI::Record");
  return *rec;
}


};
#endif

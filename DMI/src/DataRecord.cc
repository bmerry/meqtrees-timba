#define NC_SKIP_HOOKS 1
    
#include "DynamicTypeManager.h"
#include "DataRecord.h"
#include "DataField.h"

    // register as a nestable container
static NestableContainer::Register reg(TpDataRecord,True);

//##ModelId=3E9BD9150075
typedef NestableContainer::Ref NCRef;    
const NCRef NullNCRef;

//##ModelId=3C5820AD00C6
DataRecord::DataRecord (int flags)
  : NestableContainer(flags&DMI::WRITE!=0)
{
  dprintf(2)("default constructor\n");
}

//##ModelId=3C5820C7031D
DataRecord::DataRecord (const DataRecord &other, int flags, int depth)
  : NestableContainer(flags&DMI::WRITE!=0 || (flags&DMI::PRESERVE_RW!=0 && other.isWritable()))
{
  dprintf(2)("copy constructor, cloning from %s\n",other.debug(1));
  cloneOther(other,flags,depth);
}

//##ModelId=3DB93482018E
DataRecord::~DataRecord()
{
  dprintf(2)("destructor\n");
}

//##ModelId=3DB93482022F
DataRecord & DataRecord::operator=(const DataRecord &right)
{
  if( &right != this )
  {
    dprintf(2)("assignment op, cloning from %s\n",right.debug(1));
    cloneOther(right,DMI::PRESERVE_RW,0);
  }
  return *this;
}

//##ModelId=3BFBF5B600EB
void DataRecord::add (const HIID &id, const NCRef &ref, int flags)
{
  nc_writelock;
  dprintf(2)("add(%s,[%s],%x)\n",id.toString().c_str(),ref->debug(1),flags);
  FailWhen( !id.size(),"null HIID" );
  FailWhen( !isWritable(),"r/w access violation" );
  FailWhen( fields.find(id) != fields.end(), "field already exists" );
  // insert into map
  if( flags&DMI::COPYREF )
    fields[id].copy(ref,flags);
  else
    fields[id] = ref;
}

void DataRecord::add (const HIID &id,NestableContainer *pnc, int flags)
{
  nc_writelock;
  dprintf(2)("add(%s,[%s],%x)\n",id.toString().c_str(),pnc->debug(1),flags);
  FailWhen( !id.size(),"null HIID" );
  FailWhen( !isWritable(),"r/w access violation" );
  FailWhen( fields.find(id) != fields.end(), "field already exists" );
  fields[id].attach(pnc,flags);
}

//##ModelId=3BFCD4BB036F
void DataRecord::replace (const HIID &id, const NCRef &ref, int flags)
{
  nc_writelock;
  dprintf(2)("replace(%s,[%s],%x)\n",id.toString().c_str(),ref->debug(1),flags);
//  FailWhen( ref->objectType() != TpDataField && ref->objectType() != TpDataArray,
//            "illegal field object" );
  FailWhen( !id.size(),"null HIID" );
  FailWhen( !isWritable(),"r/w access violation" );
  if( flags&DMI::COPYREF )
    fields[id].copy(ref,flags);
  else
    fields[id] = ref;
}

void DataRecord::replace (const HIID &id, NestableContainer *pnc, int flags)
{
  nc_writelock;
  dprintf(2)("replace(%s,[%s],%x)\n",id.toString().c_str(),pnc->debug(1),flags);
//  FailWhen( ref->objectType() != TpDataField && ref->objectType() != TpDataArray,
//            "illegal field object" );
  FailWhen( !id.size(),"null HIID" );
  FailWhen( !isWritable(),"r/w access violation" );
  fields[id].attach(pnc,flags);
}


//##ModelId=3BB311C903BE
NCRef DataRecord::removeField (const HIID &id)
{
  nc_writelock;
  dprintf(2)("remove(%s)\n",id.toString().c_str());
  FailWhen( !id.size(),"null HIID" );
  FailWhen( !isWritable(),"r/w access violation" );
  CFMI iter = fields.find(id);
  if( iter != fields.end() )
  {
    NCRef ref(iter->second);
    fields.erase(iter->first);
    dprintf(2)("  removing %s\n",ref->debug(1));
    return ref;
  }
  Throw("field "+id.toString()+" not found");
}

//##ModelId=3C57CFFF005E
NCRef DataRecord::field (const HIID &id) const
{
  nc_readlock;
  HIID rest; bool dum;
  const NCRef &ref( resolveField(id,rest,dum,False) );
  FailWhen( !ref.valid(),"field "+id.toString()+" not found" );
  FailWhen( rest.size(),id.toString()+" does not resolve to a complete field" );
  return ref.copy(DMI::READONLY);
}

//##ModelId=3BFBF49D00A1
NCRef DataRecord::fieldWr (const HIID &id, int flags)
{
  nc_readlock;
  FailWhen( !isWritable(),"r/w access violation" );
  HIID rest; bool dum;
  const NCRef &ref( resolveField(id,rest,dum,True) );
  FailWhen( !ref.valid(),"field "+id.toString()+" not found" );
  FailWhen( rest.size(),id.toString()+" does not resolve to a complete field" );
  return ref.copy(flags);
}

//##ModelId=3C552E2D009D
const NCRef & DataRecord::resolveField (const HIID &id, HIID& rest, bool &can_write, bool must_write) const
{
  FailWhen( !id.size(),"null HIID" );
  CFMI iter = fields.find(id);
  if( iter == fields.end() )
  {
    rest = id;
    return NullNCRef;
  }
  can_write = iter->second->isWritable();
  FailWhen( must_write && !can_write,"r/w access violation" );
  rest.clear();
  return iter->second;
}

//##ModelId=3C58216302F9
int DataRecord::fromBlock (BlockSet& set)
{
  nc_writelock;
  dprintf(2)("fromBlock(%s)\n",set.debug(2));
  int nref = 1;
  fields.clear();
  // pop and cache the header block as headref
  BlockRef headref;
  set.pop(headref);
  size_t hsize = headref->size();
  FailWhen( hsize < sizeof(int),"malformed header block" );
  // get # of fields
  const char *head = static_cast<const char*>( headref->data() );
  const int *hdata = reinterpret_cast<const int *>( head );
  int nfields = *hdata++;
  const BlockFieldInfo *fieldinfo = reinterpret_cast<const BlockFieldInfo *>(hdata);
  size_t off_hids = sizeof(int) + sizeof(BlockFieldInfo)*nfields; // IDs start at this offset
  FailWhen( hsize < off_hids,"malformed header block" );
  dprintf(2)("fromBlock: %d header bytes, %d fields expected\n",hsize,nfields);
  // get fields one by one
  for( int i=0; i<nfields; i++,fieldinfo++ )
  {
    // extract ID from header block
    int idsize = fieldinfo->idsize;
    FailWhen( hsize < off_hids+idsize,"malformed header block" );
    HIID id(head+off_hids,idsize);
    off_hids += idsize;
    // create field container object
    NestableContainer *field = dynamic_cast<NestableContainer *>
        ( DynamicTypeManager::construct(fieldinfo->ftype) );
    FailWhen( !field,"cast failed: perhaps field is not a container?" );
    NCRef ref(field,DMI::ANONWR);
    // unblock and set the writable flag
    int nr = field->fromBlock(set);
    nref += nr;
    fields[id] = ref;
    dprintf(3)("%s [%s] used %d blocks\n",
          id.toString().c_str(),field->sdebug(1).c_str(),nr);
  }
  dprintf(2)("fromBlock: %d total blocks used\n",nref);
  validateContent();
  return nref;
}

//##ModelId=3C5821630371
int DataRecord::toBlock (BlockSet &set) const
{
  nc_readlock;
  dprintf(2)("toBlock\n");
  int nref = 1;
  // compute header size
  size_t hdrsize = sizeof(int) + sizeof(BlockFieldInfo)*fields.size(), 
         datasize = 0;
  for( CFMI iter = fields.begin(); iter != fields.end(); iter++ )
    datasize += iter->first.packSize();
  // allocate new header block
  SmartBlock *header = new SmartBlock(hdrsize+datasize);
  BlockRef headref(header,DMI::ANONWR);
  // store header info
  int  *hdr    = static_cast<int *>(header->data());
  char *data   = static_cast<char *>(header->data()) + hdrsize;
  *hdr++ = fields.size();
  BlockFieldInfo *fieldinfo = reinterpret_cast<BlockFieldInfo *>(hdr);
  set.push(headref);
  dprintf(2)("toBlock: %d header bytes, %d fields\n",hdrsize+datasize,fields.size());
  // store IDs and convert everything
  for( CFMI iter = fields.begin(); iter != fields.end(); iter++,fieldinfo++ )
  {
    data += fieldinfo->idsize = iter->first.pack(data,datasize);
    fieldinfo->ftype = iter->second->objectType();
    int nr1 = iter->second->toBlock(set);
    nref += nr1;
    dprintf(3)("%s [%s] generated %d blocks\n",
        iter->first.toString().c_str(),iter->second->sdebug(1).c_str(),nr1);
  }
  dprintf(2)("toBlock: %d total blocks generated\n",nref);
  return nref;
}

//##ModelId=3C58218900EB
CountedRefTarget* DataRecord::clone (int flags, int depth) const
{
  dprintf(2)("cloning new DataRecord\n");
  return new DataRecord(*this,flags,depth);
}

//##ModelId=3C582189019F
void DataRecord::privatize (int flags, int depth)
{
  nc_writelock;
  dprintf(2)("privatizing DataRecord\n");
  setWritable( (flags&DMI::WRITE)!=0 );
  if( flags&DMI::DEEP || depth>0 )
  {
    for( FMI iter = fields.begin(); iter != fields.end(); iter++ )
      iter->second.privatize(flags|DMI::LOCK,depth-1);
  }
}

//##ModelId=3C58239503D1
void DataRecord::cloneOther (const DataRecord &other, int flags, int depth)
{
  nc_writelock;
  nc_readlock1(other);
  fields.clear();
  setWritable( (flags&DMI::WRITE)!=0 || (flags&DMI::PRESERVE_RW && other.isWritable()) );
  // copy all field refs, then privatize them if depth>0.
  // For ref.copy(), clear the DMI::WRITE flag and use DMI::PRESERVE_RW instead.
  // (When depth>0, DMI::WRITE will take effect anyways via privatize().
  //  When depth=0, we must preserve the write permissions of the contents.)
  for( CFMI iter = other.fields.begin(); iter != other.fields.end(); iter++ )
  {
    NCRef & ref( fields[iter->first].copy(iter->second,
                (flags&~DMI::WRITE)|DMI::PRESERVE_RW|DMI::LOCK) );
    if( flags&DMI::DEEP || depth>0 )
      ref.privatize(flags|DMI::LOCK,depth-1);
    
  }
  validateContent();
}

//##ModelId=3C56B00E0182
const void * DataRecord::get (const HIID &id, ContentInfo &info, TypeId check_tid, int flags) const
{
  nc_lock(flags&DMI::WRITE);
  FailWhen(flags&DMI::NC_SCALAR,"can't access DataRecord in scalar mode");
  FailWhen( !id.size(),"null field id" );
  CFMI iter;
  info.size = 1;
  // "AidHash" followed by a single numeric index is field #
  if( id.size() == 2 && id[0] == AidHash && id[1].index() >= 0 )
  {
    iter = fields.begin();
    for( int i=0; i<id[1]; i++,iter++ )
      if( iter == fields.end() )
        break;
    FailWhen( iter == fields.end(),"record field number out of range");
  }
  else // else HIID is field name
    iter = fields.find(id);
  if( iter == fields.end() )
    return 0;
  NCRef &fref = const_cast<NCRef&>(iter->second);
  // This condition checks that we're not auto-privatizing a readonly container
  // (so that we can cast away const, below)
  // do unconditional privatize if required
  if( flags&DMI::PRIVATIZE )
  {
    FailWhen(!isWritable(),"can't autoprivatize in readonly record");
    fref.privatize(flags&(DMI::READONLY|DMI::WRITE|DMI::DEEP)); 
  }
  /*
  Commented out since this is plain wrong. Writability is checked for 
  separately in the if-else below.
  Removed code:
      // writability is first determined by the field ref itself, plus the field
      // An invalid ref is considered writable (we'll check for our own writability
      // below)
      info.writable = !iter->second.valid() || 
          ( iter->second.isWritable() && iter->second->isWritable() );
  */
  // default is to return an objref to the field
  if( !check_tid || check_tid == TpObjRef )
  {
    // since we're returning an objref, writability to the ref is only limited
    // by our own writability
    info.writable = isWritable();
    FailWhen(flags&DMI::WRITE && !info.writable,"write access violation"); 
    info.tid = TpObjRef;
    return &iter->second;
  }
  else // else an object type itself (or TpObject) must have been explicitly 
       // requested. 
  {
    // since we're returning a pointer to the object, writability is 
    // determined by the writability of the ref
    info.writable = !fref.valid() || fref.isWritable();
    const NestableContainer *pnc = fref.deref_p();
    info.tid = pnc->objectType();
    FailWhen(flags&DMI::WRITE && !info.writable,"write access violation"); 
    FailWhen(check_tid != info.tid && check_tid != TpObject,
        "type mismatch: expecting "+check_tid.toString()+", have " +  
        info.tid.toString() );
    return pnc;
  }
}

//##ModelId=3C7A16BB01D7
void * DataRecord::insert (const HIID &id, TypeId tid, TypeId &real_tid)
{
  nc_writelock;
  FailWhen( !id.size(),"null HIID" );
  FailWhen( fields.find(id) != fields.end(),"field "+id.toString()+" already exists" );
  if( tid != TpObjRef )
    real_tid = tid;
  // inserting a container field? Insert as a field proper
  if( isNestable(real_tid) ) 
  {
    if( tid == TpObjRef )
    {
      real_tid = TpObjRef;
      return &fields[id];
    }
    else
    {
      NestableContainer *pnc = dynamic_cast<NestableContainer *>
          ( DynamicTypeManager::construct(real_tid) );
      FailWhen(!pnc,"dynamic_cast failed");
      fields[id].attach(pnc,DMI::ANONWR|DMI::LOCK);
      return pnc;
    }
  }
  // everything else is inserted as a scalar DataField
  else     
  {
    DataField *pf = new DataField(real_tid,-1); // -1 means scalar
    fields[id].attach(pf,DMI::ANONWR|DMI::LOCK);
    ContentInfo info;
    info.tid = real_tid;
    return const_cast<void*>( pf->getn(0,info,tid,True) );
  }
}

//##ModelId=3C877D140036
bool DataRecord::remove (const HIID &id)
{
  nc_writelock;
  dprintf(2)("remove(%s)\n",id.toString().c_str());
  FailWhen( !id.size(),"null HIID" );
  FailWhen( !isWritable(),"r/w access violation" );
  // is it our field -- just remove it
  CFMI iter = fields.find(id);
  if( iter != fields.end() )
  {
    dprintf(2)("  removing %s\n",iter->second.debug(1));
    fields.erase(iter->first);
    return True;
  }
  return False;
}

//##ModelId=3C7A16C4023F
int DataRecord::size (TypeId tid) const
{
  if( !tid || tid == TpObjRef )
    return fields.size();
  return -1;
}

//##ModelId=3CA20AD703A4
bool DataRecord::getFieldIter (DataRecord::Iterator& iter, HIID& id, NCRef &ref) const
{
  if( iter.iter == fields.end() )
  {
#ifdef USE_THREADS
    iter.lock.release();
#endif
    return False;
  }
  id = iter.iter->first;
  ref.copy(iter.iter->second,DMI::PRESERVE_RW);
  iter.iter++;
  return True;
}

//##ModelId=3DB9348501B1
string DataRecord::sdebug ( int detail,const string &prefix,const char *name ) const
{
  static int nesting=0;
  nc_readlock;
  if( nesting++>1000 )
  {
    cerr<<"Too many nested DataRecord::sdebug() calls";
    abort();
  }
  string out;
  if( detail>=0 ) // basic detail
  {
    Debug::appendf(out,"%s/%08x",name?name:"DataRecord",(int)this);
  }
  if( detail >= 1 || detail == -1 )   // normal detail
  {
    Debug::append(out,isWritable()?"RW ":"RO ");
    out += Debug::ssprintf("%d fields",fields.size());
    out += " / refs "+CountedRefTarget::sdebug(-1);
  }
  if( detail >= 2 || detail <= -2 )   // high detail
  {
    // append debug info from CountedRefTarget
    string str = CountedRefTarget::sdebug(-2,prefix+"      ");
    if( str.length() )
      out += "\n"+prefix+"  refs: "+str;
    for( CFMI iter = fields.begin(); iter != fields.end(); iter++ )
    {
      if( out.length() )
        out += "\n"+prefix+"  ";
      out += iter->first.toString()+": ";
      out += iter->second->sdebug(abs(detail)-1,prefix+"          ");
    }
  }
  nesting--;
  return out;
}

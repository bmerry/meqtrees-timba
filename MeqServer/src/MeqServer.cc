#include "MeqServer.h"
#include "AID-MeqServer.h"
#include <DMI/AID-DMI.h>
#include <MEQ/AID-Meq.h>
#include <MeqNodes/AID-MeqNodes.h>
#include <MeqGen/AID-MeqGen.h>
#include <MEQ/Request.h>
#include <MEQ/Result.h>
#include <MeqNodes/ParmTable.h>
#include <DMI/BOIO.h>
#include <DMI/List.h>

    
using Debug::ssprintf;
using namespace AppAgent;
using namespace AppControlAgentVocabulary;
using namespace VisRepeaterVocabulary;
using namespace VisVocabulary;
using namespace VisAgent;
    
namespace Meq 
{
  
static int dum =  aidRegistry_MeqServer() + 
                  aidRegistry_Meq() + 
                  aidRegistry_MeqNodes() + 
                  aidRegistry_MeqGen();

const HIID DataProcessingError = AidData|AidProcessing|AidError;
  
InitDebugContext(MeqServer,"MeqServer");

// this flag can be set in the input record of all commands dealing with
// individual nodes to have the new node state included in the command result.
// (The exception is Node.Get.State, which returns the node state anyway)
const HIID FGetState = AidGet|AidState;
// this flag can be set in the input record of most commands to request
// a forest status update in the reply 
// Set to 1 to get basic status in field forest_status
// Set to 2 to also get the full forest state record in field forest_state
// (The exception is Node.Get.State, which returns the node state as the 
// top-level record, Node.Create, where the input record is the node state,
// and Set.Forest.State, which returns the full status anyway)
const HIID FGetForestStatus = AidGet|AidForest|AidStatus;

// this field is set to True in the output record of a command
// whenever the forest itself has changed (i.e. nodes created or deleted, etc.)
const HIID FForestChanged = AidForest|AidChanged;

// this field is set to True in the output record of a command when 
// publishing is disabled for all nodes.
const HIID FDisabledAllPublishing = AidDisabled|AidAll|AidPublishing;

// ...as field node_state
const HIID FNodeState = AidNode|AidState;

//const HIID FBreakpoint = AidBreakpoint;
const HIID FSingleShot = AidSingle|AidShot;

MeqServer * MeqServer::mqs_ = 0;

// application run-states
const int AppState_Idle    = -( AidIdle.id() );
const int AppState_Stream  = -( AidStream.id() );
const int AppState_Execute = -( AidExecute.id() );
const int AppState_Debug   = -( AidDebug.id() );
  
//##ModelId=3F5F195E0140
MeqServer::MeqServer()
    : data_mux(forest)
{
  if( mqs_ )
    Throw1("A singleton MeqServer has already been created");
  mqs_ = this;
  
  command_map["Get.Forest.State"] = &MeqServer::getForestState;
  command_map["Set.Forest.State"] = &MeqServer::setForestState;
  
  command_map["Create.Node"] = &MeqServer::createNode;
  command_map["Delete.Node"] = &MeqServer::deleteNode;
  command_map["Resolve"] = &MeqServer::resolve;
  command_map["Get.Node.List"] = &MeqServer::getNodeList;
  command_map["Get.Forest.Status"] = &MeqServer::getForestStatus;
  command_map["Get.NodeIndex"] = &MeqServer::getNodeIndex;

  command_map["Disable.Publish.Results"] = &MeqServer::disablePublishResults;
  command_map["Save.Forest"] = &MeqServer::saveForest;
  command_map["Load.Forest"] = &MeqServer::loadForest;
  command_map["Clear.Forest"] = &MeqServer::clearForest;

  // per-node commands  
  command_map["Node.Get.State"] = &MeqServer::nodeGetState;
  command_map["Node.Set.State"] = &MeqServer::nodeSetState;
  command_map["Node.Execute"] = &MeqServer::nodeExecute;
  command_map["Node.Clear.Cache"] = &MeqServer::nodeClearCache;
  command_map["Node.Publish.Results"] = &MeqServer::publishResults;
  command_map["Node.Set.Breakpoint"] = &MeqServer::nodeSetBreakpoint;
  command_map["Node.Clear.Breakpoint"] = &MeqServer::nodeClearBreakpoint;
  
  command_map["Debug.Set.Level"] = &MeqServer::debugSetLevel;
  command_map["Debug.Single.Step"] = &MeqServer::debugSingleStep;
  command_map["Debug.Next.Node"] = &MeqServer::debugNextNode;
  command_map["Debug.Until.Node"] = &MeqServer::debugUntilNode;
  command_map["Debug.Continue"] = &MeqServer::debugContinue;
  
  debug_next_node = 0;
}

//##ModelId=3F6196800325
Node & MeqServer::resolveNode (bool &getstate,const DMI::Record &rec)
{
  int nodeindex = rec[AidNodeIndex].as<int>(-1);
  string name = rec[AidName].as<string>("");
  getstate = rec[FGetState].as<bool>(false);
  if( nodeindex>0 )
  {
    Node &node = forest.get(nodeindex);
    FailWhen( name.length() && node.name() != name,"node specified by index is "+ 
        node.name()+", which does not match specified name "+name); 
    return node;
  }
  FailWhen( !name.length(),"either nodeindex or name must be specified");
  cdebug(3)<<"looking up node name "<<name<<endl;
  return forest.findNode(name);
}


void MeqServer::setForestState (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  cdebug(3)<<"setForestState()"<<endl;
  DMI::Record::Ref ref = in[AidState].ref();
  forest.setState(ref);
  fillForestStatus(out(),2);
}

void MeqServer::getForestState (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  fillForestStatus(out(),2);
}

void MeqServer::getForestStatus (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  fillForestStatus(out(),in[FGetForestStatus].as<int>(1));
}

void MeqServer::createNode (DMI::Record::Ref &out,DMI::Record::Ref &initrec)
{
  cdebug(2)<<"creating node ";
  cdebug(3)<<initrec->sdebug(3);
  cdebug(2)<<endl;
  int nodeindex;
  Node & node = forest.create(nodeindex,initrec);
  // form a response message
  const string & name = node.name();
  string classname = node.className();
  
  out[AidNodeIndex] = nodeindex;
  out[AidName] = name;
  out[AidClass] = classname;
  out[AidMessage] = ssprintf("created node %d:%s of class %s",
                        nodeindex,name.c_str(),classname.c_str());
  out[FForestChanged] = true;
}

void MeqServer::deleteNode (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  int nodeindex = (*in)[AidNodeIndex].as<int>(-1);
  if( nodeindex<0 )
  {
    string name = (*in)[AidName].as<string>("");
    cdebug(3)<<"looking up node name "<<name<<endl;
    FailWhen( !name.length(),"either nodeindex or name must be specified");
    nodeindex = forest.findIndex(name);
    FailWhen( nodeindex<0,"node '"+name+"' not found");
  }
  const Node::Ref &noderef = forest.getRef(nodeindex);
  string name = noderef->name();
  cdebug(2)<<"deleting node "<<name<<"("<<nodeindex<<")\n";
  // remove from forest
  forest.remove(nodeindex);
  out[AidMessage] = ssprintf("node %d (%s): deleted",nodeindex,name.c_str());
  // fill optional responce fields
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
  out[FForestChanged] = true;
}

void MeqServer::nodeGetState (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  bool getstate;
  Node & node = resolveNode(getstate,*in);
  cdebug(3)<<"getState for node "<<node.name()<<" ";
  cdebug(4)<<in->sdebug(3);
  cdebug(3)<<endl;
  out.attach(node.syncState());
  cdebug(5)<<"Returned state is: "<<out->sdebug(20)<<endl;
}

void MeqServer::getNodeIndex (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  string name = in[AidName].as<string>();
  out[AidNodeIndex] = forest.findIndex(name);
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

void MeqServer::nodeSetState (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  DMI::Record::Ref rec = in;
  bool getstate;
  Node & node = resolveNode(getstate,*rec);
  cdebug(3)<<"setState for node "<<node.name()<<endl;
  DMI::Record::Ref ref = rec[AidState].ref();
  node.setState(ref);
  if( getstate )
    out[FNodeState] <<= node.syncState();
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

//##ModelId=3F98D91A03B9
void MeqServer::resolve (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  DMI::Record::Ref rec = in;
  bool getstate;
  Node & node = resolveNode(getstate,*rec);
  cdebug(2)<<"resolve for node "<<node.name()<<endl;
  // create request for the commands. Note that request ID will be null,
  // meaning it will ignore cache and go up the entire tree
  node.resolve(rec,0);
  cdebug(3)<<"resolve complete"<<endl;
  out[AidMessage] = ssprintf("node %d (%s): resolve complete",
      node.nodeIndex(),node.name().c_str());
  if( getstate )
    out[FNodeState] <<= node.syncState();
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

void MeqServer::getNodeList (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  cdebug(2)<<"getNodeList: building list"<<endl;
  DMI::Record &list = out <<= new DMI::Record;
  int content = 
    ( in[AidNodeIndex].as<bool>(true) ? Forest::NL_NODEINDEX : 0 ) | 
    ( in[AidName].as<bool>(true) ? Forest::NL_NAME : 0 ) | 
    ( in[AidClass].as<bool>(true) ? Forest::NL_CLASS : 0 ) | 
    ( in[AidChildren].as<bool>(false) ? Forest::NL_CHILDREN : 0 ) |
    ( in[FControlStatus].as<bool>(false) ? Forest::NL_CONTROL_STATUS : 0 );
  int count = forest.getNodeList(list,content);
  cdebug(2)<<"getNodeList: got list of "<<count<<" nodes"<<endl;
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

//##ModelId=400E5B6C015E
void MeqServer::nodeExecute (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  int old_control_state = control().state();
  control().setState(AppState_Execute,true);
  try
  {
    DMI::Record::Ref rec = in;
    bool getstate;
    Node & node = resolveNode(getstate,*rec);
    cdebug(2)<<"nodeExecute for node "<<node.name()<<endl;
    // take request object out of record
    Request &req = rec[AidRequest].as_wr<Request>();
    if( Debug(0) )
    {
      cdebug(3)<<"    request is "<<req.sdebug(DebugLevel-1,"    ")<<endl;
      if( req.hasCells() )
      {
        cdebug(3)<<"    request cells are: "<<req.cells();
      }
    }
    Result::Ref resref;
    int flags = node.execute(resref,req);
    cdebug(2)<<"  execute() returns flags "<<ssprintf("0x%x",flags)<<endl;
    cdebug(3)<<"    result is "<<resref.sdebug(DebugLevel-1,"    ")<<endl;
    if( DebugLevel>3 && resref.valid() )
    {
      for( int i=0; i<resref->numVellSets(); i++ ) 
      {
        const VellSet &vs = resref->vellSet(i);
        if( vs.isFail() ) {
          cdebug(4)<<"  vellset "<<i<<": FAIL"<<endl;
        } else {
          cdebug(4)<<"  vellset "<<i<<": "<<vs.getValue()<<endl;
        }
      }
    }
    out[AidResult|AidCode] = flags;
    if( resref.valid() )
      out[AidResult] <<= resref;
    out[AidMessage] = ssprintf("node %d (%s): execute() returns %x",
        node.nodeIndex(),node.name().c_str(),flags);
    if( getstate )
      out[FNodeState] <<= node.syncState();
    fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
  }
  catch( std::exception &exc )
  {
    control().setState(old_control_state);
//    old_paused ? control().pause() : control().resume();
    throw;
  }
  control().setState(old_control_state);
//  old_paused ? control().pause() : control().resume();
}


//##ModelId=400E5B6C01DD
void MeqServer::nodeClearCache (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  DMI::Record::Ref rec = in;
  bool getstate;
  Node & node = resolveNode(getstate,*rec);
  bool recursive = (*rec)[FRecursive].as<bool>(false);
  cdebug(2)<<"nodeClearCache for node "<<node.name()<<", recursive: "<<recursive<<endl;
  node.clearCache(recursive);
  out[AidMessage] = ssprintf("node %d (%s): cache cleared%s",
      node.nodeIndex(),node.name().c_str(),recursive?" recursively":"");
  if( getstate )
    out[FNodeState] <<= node.syncState();
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

//##ModelId=400E5B6C0247
void MeqServer::saveForest (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  if( !debug_stack.empty() )
    Throw1("can't execute Save.Forest while debugging");
  string filename = (*in)[FFileName].as<string>();
  cdebug(1)<<"saving forest to file "<<filename<<endl;
  postMessage(ssprintf("saving forest to file %s, please wait",filename.c_str()));
  BOIO boio(filename,BOIO::WRITE);
  int nsaved = 0;
  // write header record
  DMI::Record header;
  header["Forest.Header.Version"] = 1;
  boio << header;
  // write forest state
  boio << forest.state();
  // write all nodes
  for( int i=1; i<=forest.maxNodeIndex(); i++ )
    if( forest.valid(i) )
    {
      Node &node = forest.get(i);
      cdebug(3)<<"saving node "<<node.name()<<endl;
      boio << node.syncState();
      nsaved++;
    }
  cdebug(1)<<"saved "<<nsaved<<" nodes to file "<<filename<<endl;
  out[AidMessage] = ssprintf("saved %d nodes to file %s",
      nsaved,filename.c_str());
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
  out[FForestChanged] = true;
}

//##ModelId=400E5B6C02B3
void MeqServer::loadForest (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  if( !debug_stack.empty() )
    Throw1("can't execute Load.Forest while debugging");
  string filename = (*in)[FFileName].as<string>();
  cdebug(1)<<"loading forest from file "<<filename<<endl;
  postMessage(ssprintf("loading forest from file %s, please wait",filename.c_str()));
  forest.clear();
  int nloaded = 0;
  DMI::Record::Ref ref;
  std::string fmessage;
  // open file
  BOIO boio(filename,BOIO::READ);
  // get header record out
  if( ! (boio >> ref) )
  {
    Throw("no records in file");
  }
  // is this a version record?
  int version = ref["Forest.Header.Version"].as<int>(-1);
  if( version >=1 )
  {
    // version 1+: forest state comes first
    if( !(boio >> ref) )
    {
      Throw("no forest state in file");
    }
    forest.setState(ref,true);
    // then get next node record for loop below
    if( !(boio >> ref) )
      ref.detach();
    fmessage = "loaded %d nodes and forest state from file %s";
  }
  else
  {
    // else version 0: nothing but node records in here, so fall through
    fmessage = "loaded %d nodes from old-style file %s";
  }
  // ok, at this point we expect a bunch of node records
  do
  {
    int nodeindex;
    // create the node, while
    Node & node = forest.create(nodeindex,ref,true);
    cdebug(3)<<"loaded node "<<node.name()<<endl;
    nloaded++;
  }
  while( boio >> ref );
  cdebug(2)<<"loaded "<<nloaded<<" nodes, setting child links"<<endl;
  for( int i=1; i<=forest.maxNodeIndex(); i++ )
    if( forest.valid(i) )
    {
      Node &node = forest.get(i);
      cdebug(3)<<"setting children for node "<<node.name()<<endl;
      node.relinkChildren();
    }
  out[AidMessage] = ssprintf(fmessage.c_str(),nloaded,filename.c_str());
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
  out[FForestChanged] = true;
}

//##ModelId=400E5B6C0324
void MeqServer::clearForest (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  if( !debug_stack.empty() )
    Throw1("can't execute Clear.Forest while debugging");
  cdebug(1)<<"clearing forest: deleting all nodes"<<endl;
  forest.clear();
// ****
// **** added this to relinquish parm tables --- really ought to go away
  ParmTable::closeTables();
// ****
  out[AidMessage] = "all nodes deleted";
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
  out[FForestChanged] = true;
}

void MeqServer::publishResults (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  DMI::Record::Ref rec = in;
  bool getstate;
  Node & node = resolveNode(getstate,*rec);
  bool enable = rec[FEnable].as<bool>(true);
  const HIID &evid = rec[FEventId].as<HIID>(EvNodeResult);
  if( enable )
  {
    cdebug(2)<<"publishResults: enabling for node "<<node.name()<<endl;
    node.addResultSubscriber(EventSlot(evid,this));
    out[AidMessage] = ssprintf("node %d (%s): publishing results",
        node.nodeIndex(),node.name().c_str());
  }
  else
  {
    cdebug(2)<<"publishResults: disabling for node "<<node.name()<<endl;
    node.removeResultSubscriber(EventSlot(evid,this));
    out[AidMessage] = ssprintf("node %d (%s): no longer publishing results",
        node.nodeIndex(),node.name().c_str());
  }
  if( getstate )
    out[FNodeState] <<= node.syncState();
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

void MeqServer::disablePublishResults (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  cdebug(2)<<"disablePublishResults: disabling for all nodes"<<endl;
  for( int i=0; i<=forest.maxNodeIndex(); i++ )
    if( forest.valid(i) )
      forest.get(i).removeResultSubscriber(this);
  out[AidMessage] = "nodes no longer publishing results";
  out[FDisabledAllPublishing] = true;
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

void MeqServer::nodeSetBreakpoint (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  DMI::Record::Ref rec = in;
  bool getstate;
  Node & node = resolveNode(getstate,*rec);
  int bpmask = rec[FBreakpoint].as<int>(Node::breakpointMask(Node::CS_ES_REQUEST));
  bool oneshot = rec[FSingleShot].as<bool>(false);
  cdebug(2)<<"nodeSetBreakpoint: node "<<node.name()<<" mask "<<bpmask<<(oneshot?" single-shot\n":"\n");
  node.setBreakpoint(bpmask,oneshot);
  if( getstate )
    out[FNodeState] <<= node.syncState();
  out[AidMessage] = Debug::ssprintf("node %s: set %sbreakpoint %X; "
        "new bp mask is %X",
        node.name().c_str(),oneshot?"one-shot":"",
        bpmask,node.getBreakpoints(oneshot));
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

void MeqServer::nodeClearBreakpoint (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  DMI::Record::Ref rec = in;
  bool getstate;
  Node & node = resolveNode(getstate,*rec);
  int bpmask = rec[FBreakpoint].as<int>(Node::CS_BP_ALL);
  bool oneshot = rec[FSingleShot].as<bool>(false);
  cdebug(2)<<"nodeClearBreakpoint: node "<<node.name()<<" mask "<<bpmask<<(oneshot?" single-shot\n":"\n");
  node.clearBreakpoint(bpmask,oneshot);
  if( getstate )
    out[FNodeState] <<= node.syncState();
  out[AidMessage] = Debug::ssprintf("node %s: clearing breakpoint %X; "
        "new bp mask is %X",node.name().c_str(),bpmask,node.getBreakpoints(oneshot));
  fillForestStatus(out(),in[FGetForestStatus].as<int>(0));
}

void MeqServer::debugSetLevel (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  cdebug(1)<<"setting debugging level"<<endl;
  int verb = in[AidDebug|AidLevel].as<int>();
  verb = std::min(verb,2);
  verb = std::max(verb,0);
  forest.setDebugLevel(verb);
  std::string msg = Debug::ssprintf("debug level %d set",verb);
  if( !verb )
    msg += " (disabled)";
  out[AidMessage] = msg;
  fillForestStatus(out(),in[FGetForestStatus].as<int>(1));
}


void MeqServer::debugContinue (DMI::Record::Ref &,DMI::Record::Ref &)
{
// continue always allowed, since it doesn't hurt anything
//  if( in_debugger )
//    Throw1("can't execute a Continue command when not debugging");
  // clear all global breakpoints and continue
  forest.clearBreakpoint(Node::CS_ALL,false);
  forest.clearBreakpoint(Node::CS_ALL,true);
  debug_continue = true;
}

void MeqServer::debugSingleStep (DMI::Record::Ref &,DMI::Record::Ref &in)
{
  if( debug_stack.empty() )
    Throw1("can't execute Debug.Single.Step command when not debugging");
  // set a global one-shot breakpoint on everything
  forest.setBreakpoint(Node::CS_ALL,true);
  debug_next_node = 0;
  debug_continue = true;
}

void MeqServer::debugNextNode (DMI::Record::Ref &,DMI::Record::Ref &in)
{
  if( debug_stack.empty() )
    Throw1("can't execute Debug.Next.Node command when not debugging");
  // set a global breakpoint on everything, will keep firing until a different
  // node is reached (or until a local node breakpoint occurs)
  forest.setBreakpoint(Node::CS_ALL);
  debug_next_node = debug_stack.front().node;
  debug_continue = true;
}

void MeqServer::debugUntilNode (DMI::Record::Ref &out,DMI::Record::Ref &in)
{
  if( debug_stack.empty() )
    Throw1("can't execute Debug.Until.Node command when not debugging");
  bool getstate;
  Node & node = resolveNode(getstate,*in);
  // set one-shot breakpoint on anything in this node
  node.setBreakpoint(Node::CS_ALL,true);
  // clear all global breakpoints and continue
  forest.clearBreakpoint(Node::CS_ALL,false);
  forest.clearBreakpoint(Node::CS_ALL,true);
  debug_continue = true;
}

int MeqServer::receiveEvent (const EventIdentifier &evid,const ObjRef &evdata,void *) 
{
  cdebug(4)<<"received event "<<evid.id()<<endl;
  control().postEvent(evid.id(),evdata);
  return 1;
}

void MeqServer::postMessage (const std::string &msg,const HIID &type,AtomicID category)
{
  DMI::Record::Ref out(new DMI::Record);
  if( type == HIID(AidError) )
    out[AidError] = msg;
  else
    out[AidMessage] = msg;
  control().postEvent(type,out,category);
}

void MeqServer::reportNodeStatus (Node &node,int oldstat,int newstat)
{
  if( forest.debugLevel() <= 0 )
    return;
  // check what's changed
  int changemask = oldstat^newstat;
  // at verbosity level 1, only report changes to result type
  // at level>1, report changes to anything
  if( changemask&Node::CS_RES_MASK ||
      ( forest.debugLevel()>1 && changemask )  )
  {
    // node status reported within the message ID itself. Message payload is empty
    HIID ev = EvNodeStatus | node.nodeIndex() | newstat;
    if( forest.debugLevel()>1 )
      ev |= node.currentRequestId();
    control().postEvent(ev,ObjRef(),AidDebug);
  }
}

void MeqServer::fillForestStatus  (DMI::Record &rec,int level)
{
  if( !level )
    return;
  if( level>1 )
    rec[AidForest|AidState] = forest.state();
  DMI::Record &fst = rec[AidForest|AidStatus] <<= new DMI::Record;
  fst[AidState] = control().state();
  fst[AidState|AidString] = control().stateString();
  fst[AidRunning] = control().state() == AppState_Stream || 
                    control().state() == AppState_Execute ||
                    control().state() == AppState_Debug;
  fst[AidDebug|AidLevel] = forest.debugLevel();
  if( forest.debugLevel() )
  {
    DMI::List &stack = fst[AidDebug|AidStack] <<= new DMI::List;
    int i=0;
    for( DebugStack::const_iterator iter = debug_stack.begin(); 
         iter != debug_stack.end(); iter++,i++ )
    {
      DMI::Record &entry = stack[i] <<= new DMI::Record;
      entry[AidName] = iter->node->name();
      entry[AidNodeIndex] = iter->node->nodeIndex();
      entry[AidControl|AidStatus] = iter->node->getControlStatus();
      // currently stopped node gets its state too
      if( !i )
        entry[AidState] <<= iter->node->syncState();
    }
  }
}

void MeqServer::processBreakpoint (Node &node,int bpmask,bool global)
{
  // if forest.debugLevel is 0, debugging has been disabled -- ignore the breakpoint
  if( forest.debugLevel() <= 0 )
    return;
  // return immediately if we hit a global breakpoint after a next-node
  // command, and node hasn't changed yet
  if( global && debug_next_node == &node )
    return;
  // suspend input stream on first breakpoint
  if( debug_stack.empty() )
    input().suspend();
  // allocate a new debug frame
  debug_stack.push_front(DebugFrame());
  DebugFrame & frame = debug_stack.front();
  frame.node = &node;
  debug_continue = false;
  // post event indicating we're stopped in the debugger
  DMI::Record::Ref ref;
  DMI::Record &rec = ref <<= new DMI::Record;
  fillForestStatus(rec);
  rec[AidMessage] = "stopped at " + node.name() + ":" + node.getStrExecState();
  control().postEvent(EvDebugStop,ref);
  int old_state = control().state();
  control().setState(AppState_Debug);
  input().suspend();
  // keep on processing commands until asked to continue
  while( forest.debugLevel() > 0 && control().state() > 0 && !debug_continue )  // while in a running state
  {
    processCommands();
  }
  // clear debug frame 
  debug_stack.pop_front();
  if( debug_stack.empty() )
    input().resume();
  control().setState(old_state);
}

// static callbacks mapping to methods of the global MeqServer object
void MeqServer::mqs_reportNodeStatus (Node &node,int oldstat,int newstat)
{
  mqs_->reportNodeStatus(node,oldstat,newstat);
}

void MeqServer::mqs_processBreakpoint (Node &node,int bpmask,bool global)
{
  mqs_->processBreakpoint(node,bpmask,global);
}

void MeqServer::processCommands ()
{
  // check for any commands from the control agent
  HIID cmdid;
  DMI::Record::Ref cmddata;
  if( control().getCommand(cmdid,cmddata,AppEvent::WAIT) == AppEvent::SUCCESS 
      && cmdid.matches(AppCommandMask) )
  {
    // strip off the App.Control.Command prefix -- the -1 is not very
    // nice because it assumes a wildcard is the last thing in the mask.
    // Which it usually will be
    cmdid = cmdid.subId(AppCommandMask.length()-1);
    cdebug(3)<<"received app command "<<cmdid.toString('.')<<endl;
    int request_id = 0;
    bool silent = false;
    DMI::Record::Ref retval(DMI::ANONWR);
    bool have_error = true;
    string error_str;
    int oldstate = control().state();
    try
    {
      request_id = cmddata[FRequestId].as<int>(0);
      ObjRef ref = cmddata[FArgs].remove();
      silent     = cmddata[FSilent].as<bool>(false);
      DMI::Record::Ref args;
      if( ref.valid() )
      {
        FailWhen(!ref->objectType()==TpDMIRecord,"invalid args field");
        args = ref.ref_cast<DMI::Record>();
      }
      CommandMap::const_iterator iter = command_map.find(cmdid);
      if( iter != command_map.end() )
      {
        // execute the command, catching any errors
        (this->*(iter->second))(retval,args);
        // got here? success!
        have_error = false;
      }
      else // command not found
        error_str = "unknown command "+cmdid.toString('.');
    }
    catch( std::exception &exc )
    {
      have_error = true;
      error_str = exc.what();
    }
    catch( ... )
    {
      have_error = true;
      error_str = "unknown exception while processing command";
    }
    control().setState(oldstate);
    // send back reply if quiet flag has not been raised;
    // errors are always sent back
    if( !silent || have_error )
    {
      // in case of error, insert error message into return value
      if( have_error )
        retval[AidError] = error_str;
      HIID reply_id = CommandResultPrefix|cmdid;
      if( request_id )
        reply_id |= request_id;
      control().postEvent(reply_id,retval);
    }
  }
}

//##ModelId=3F608106021C
void MeqServer::run ()
{
  // connect forest events to data_mux slots (so that the mux can register
  // i/o nodes)
  forest.addSubscriber(AidCreate,EventSlot(VisDataMux::EventCreate,&data_mux));
  forest.addSubscriber(AidDelete,EventSlot(VisDataMux::EventDelete,&data_mux));
  forest.setDebuggingCallbacks(mqs_reportNodeStatus,mqs_processBreakpoint);
  
  verifySetup(true);
  DMI::Record::Ref initrec;
  HIID output_event;
  string doing_what,error_str;
  bool have_error;
  // keep running as long as start() on the control agent succeeds
  while( control().start(initrec) == AppState::RUNNING )
  {
    have_error = false;
    try
    {
      // [re]initialize i/o agents with record returned by control
      if( initrec[input().initfield()].exists() )
      {
        doing_what = "initializing input agent";
        output_event = InputInitFailed;
        cdebug(1)<<doing_what<<endl;
        if( !input().init(*initrec) )
          Throw("init failed");
      }
      if( initrec[output().initfield()].exists() )
      {
        doing_what = "initializing output agent";
        output_event = OutputInitFailed;
        cdebug(1)<<doing_what<<endl;
        if( !output().init(*initrec) )
          Throw("init failed");
      }
    }
    catch( std::exception &exc )
    { have_error = true; error_str = exc.what(); }
    catch( ... )
    { have_error = true; error_str = "unknown exception"; }
    // in case of error, generate event and go back to start
    if( have_error )
    {
      error_str = "error " + doing_what + ": " + error_str;
      cdebug(1)<<error_str<<", waiting for reinitialization"<<endl;
      DMI::Record::Ref retval(DMI::ANONWR);
      retval[AidError] = error_str;
      control().postEvent(output_event,retval);
      continue;
    }
    
    // init the data mux
    data_mux.init(*initrec,input(),output(),control());
    // get params from control record
    int ntiles = 0;
    DMI::Record::Ref header;
    bool reading_data=false;
    HIID vdsid,datatype;
    
    control().setStatus(StStreamState,"none");
    control().setStatus(StNumTiles,0);
    control().setStatus(StVDSID,vdsid);
    
    control().setState(AppState_Idle);
    // run main loop
    while( control().state() > 0 )  // while in a running state
    {
      // check for any incoming data
      DMI::Record::Ref eventrec;
      eventrec.detach();
      cdebug(4)<<"checking input\n";
      HIID id;
      ObjRef ref,header_ref;
      int instat = input().getNext(id,ref,0,AppEvent::WAIT);
      if( instat > 0 )
      { 
        string output_message;
        HIID output_event;
        have_error = false;
        int retcode = 0;
        try
        {
          
          // process data event
          if( instat == DATA )
          {
            doing_what = "processing input DATA event";
            VisCube::VTile::Ref tileref = ref.ref_cast<VisCube::VTile>();
            cdebug(4)<<"received tile "<<tileref->tileId()<<endl;
            if( !reading_data )
            {
              control().setState(AppState_Stream);
              control().setStatus(StStreamState,"DATA");
              reading_data = true;
            }
            ntiles++;
            if( !(ntiles%100) )
              control().setStatus(StNumTiles,ntiles);
            // deliver tile to data mux
            retcode = data_mux.deliverTile(tileref);
          }
          else if( instat == FOOTER )
          {
            doing_what = "processing input FOOTER event";
            cdebug(2)<<"received footer"<<endl;
            reading_data = false;
            eventrec <<= new DMI::Record;
            if( header.valid() )
              eventrec[AidHeader] <<= header.copy();
            if( ref.valid() )
              eventrec[AidFooter] <<= ref.copy();
            retcode = data_mux.deliverFooter(*(ref.ref_cast<DMI::Record>()));
            output_event = DataSetFooter;
            output_message = ssprintf("received footer for dataset %s, %d tiles written",
                id.toString('.').c_str(),ntiles);
            control().setStatus(StStreamState,"END");
            control().setStatus(StNumTiles,ntiles);
            control().setState(AppState_Idle);
            // post to output only if writing some data
          }
          else if( instat == HEADER )
          {
            doing_what = "processing input HEADER event";
            cdebug(2)<<"received header"<<endl;
            reading_data = false;
            header = ref;
            eventrec <<= new DMI::Record;
            eventrec[AidHeader] <<= header.copy();
            retcode = data_mux.deliverHeader(*header);
            output_event = DataSetHeader;
            output_message = "received header for dataset "+id.toString('.');
            if( !datatype.empty() )
              output_message += ", " + datatype.toString('.');
            control().setStatus(StStreamState,"HEADER");
            control().setStatus(StNumTiles,ntiles=0);
            control().setStatus(StVDSID,vdsid = id);
            control().setStatus(FDataType,datatype);
            control().setState(AppState_Stream);
          }
          // generate output event if one was queued up
          if( !output_event.empty() )
            postDataEvent(output_event,output_message,eventrec);
          // throw exception if a fail was indicated
          if( retcode&Node::RES_FAIL )
          {
            Throw("one or more Sink(s) or Spigot(s) reported a FAIL");
          }
        }
        catch( std::exception &exc )
        {
          have_error = true;
          error_str = exc.what();
          cdebug(2)<<"error while " + doing_what + ": "<<exc.what()<<endl;
        }
        catch( ... )
        {
          have_error = true;
          error_str = "unknown exception";
          cdebug(2)<<"unknown error while " + doing_what<<endl;
        }
        // in case of error, generate event
        if( have_error )
        {
          DMI::Record::Ref retval(DMI::ANONWR);
          retval[AidError] = error_str;
          retval[AidData|AidId] = id;
          control().postEvent(DataProcessingError,retval);
        }
      }
      processCommands();
    }
    // go back up for another start() call
  }
  cdebug(1)<<"exiting with control state "<<control().stateString()<<endl;
  control().close();
  forest.removeSubscriber(AidCreate,&data_mux);
  forest.removeSubscriber(AidDelete,&data_mux);
}

//##ModelId=3F5F195E0156
string MeqServer::sdebug(int detail, const string &prefix, const char *name) const
{
  return "MeqServer";
}

};

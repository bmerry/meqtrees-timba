    // This file is generated automatically -- do not edit
    // Generated by /home/oms/LOFAR/autoconf_share/../Timba/DMI/aid/build_aid_maps.pl
    #include <DMI/AtomicID.h>
    #include <DMI/TypeInfo.h>
    #include <DMI/DynamicTypeManager.h>
    #include <DMI/Packer.h>
#include "TableFormat.h"
DMI::BObj * __construct_VisCubeTableFormat (int n) { return n>0 ? new VisCube::TableFormat [n] : new VisCube::TableFormat; }
#include "ColumnarTableTile.h"
DMI::BObj * __construct_VisCubeColumnarTableTile (int n) { return n>0 ? new VisCube::ColumnarTableTile [n] : new VisCube::ColumnarTableTile; }
#include "VTile.h"
DMI::BObj * __construct_VisCubeVTile (int n) { return n>0 ? new VisCube::VTile [n] : new VisCube::VTile; }
#include "VCube.h"
DMI::BObj * __construct_VisCubeVCube (int n) { return n>0 ? new VisCube::VCube [n] : new VisCube::VCube; }
#include "VCubeSet.h"
DMI::BObj * __construct_VisCubeVCubeSet (int n) { return n>0 ? new VisCube::VCubeSet [n] : new VisCube::VCubeSet; }
    using namespace DMI;
  
    int aidRegistry_VisCube ()
    {
      static int res = 

        AtomicID::registerId(-1160,"UVData")+
        AtomicID::registerId(-1156,"UVSet")+
        AtomicID::registerId(-1153,"Row")+
        AtomicID::registerId(-1132,"Raw")+
        AtomicID::registerId(-1148,"Sorted")+
        AtomicID::registerId(-1199,"Unsorted")+
        AtomicID::registerId(-1126,"Time")+
        AtomicID::registerId(-1136,"Timeslot")+
        AtomicID::registerId(-1165,"Channel")+
        AtomicID::registerId(-1163,"Num")+
        AtomicID::registerId(-1142,"Control")+
        AtomicID::registerId(-1128,"MS")+
        AtomicID::registerId(-1150,"Integrate")+
        AtomicID::registerId(-1134,"Flag")+
        AtomicID::registerId(-1159,"Exposure")+
        AtomicID::registerId(-1158,"Receptor")+
        AtomicID::registerId(-1202,"Antenna")+
        AtomicID::registerId(-1179,"IFR")+
        AtomicID::registerId(-1193,"SPW")+
        AtomicID::registerId(-1183,"Field")+
        AtomicID::registerId(-1123,"UVW")+
        AtomicID::registerId(-1103,"Data")+
        AtomicID::registerId(-1181,"Integrated")+
        AtomicID::registerId(-1198,"Point")+
        AtomicID::registerId(-1162,"Source")+
        AtomicID::registerId(-1180,"Segment")+
        AtomicID::registerId(-1188,"Corr")+
        AtomicID::registerId(-1122,"Name")+
        AtomicID::registerId(-1201,"Header")+
        AtomicID::registerId(-1135,"Footer")+
        AtomicID::registerId(-1124,"Patch")+
        AtomicID::registerId(-1115,"XX")+
        AtomicID::registerId(-1118,"YY")+
        AtomicID::registerId(-1170,"XY")+
        AtomicID::registerId(-1175,"YX")+
        AtomicID::registerId(-1119,"Chunk")+
        AtomicID::registerId(-1143,"Indexing")+
        AtomicID::registerId(-1061,"Index")+
        AtomicID::registerId(-1173,"Subtable")+
        AtomicID::registerId(-1085,"Type")+
        AtomicID::registerId(-1131,"Station")+
        AtomicID::registerId(-1155,"Mount")+
        AtomicID::registerId(-1169,"Pos")+
        AtomicID::registerId(-1195,"Offset")+
        AtomicID::registerId(-1147,"Dish")+
        AtomicID::registerId(-1197,"Diameter")+
        AtomicID::registerId(-1196,"Feed")+
        AtomicID::registerId(-1187,"Interval")+
        AtomicID::registerId(-1190,"Polarization")+
        AtomicID::registerId(-1145,"Response")+
        AtomicID::registerId(-1174,"Angle")+
        AtomicID::registerId(-1154,"Ref")+
        AtomicID::registerId(-1177,"Freq")+
        AtomicID::registerId(-1161,"Width")+
        AtomicID::registerId(-1176,"Bandwidth")+
        AtomicID::registerId(-1200,"Effective")+
        AtomicID::registerId(-1191,"Resolution")+
        AtomicID::registerId(-1139,"Total")+
        AtomicID::registerId(-1182,"Net")+
        AtomicID::registerId(-1117,"Sideband")+
        AtomicID::registerId(-1114,"IF")+
        AtomicID::registerId(-1133,"Conv")+
        AtomicID::registerId(-1189,"Chain")+
        AtomicID::registerId(-1166,"Group")+
        AtomicID::registerId(-1152,"Desc")+
        AtomicID::registerId(-1120,"Code")+
        AtomicID::registerId(-1144,"Poly")+
        AtomicID::registerId(-1164,"Delay")+
        AtomicID::registerId(-1127,"Dir")+
        AtomicID::registerId(-1129,"Phase")+
        AtomicID::registerId(-1171,"Pointing")+
        AtomicID::registerId(-1194,"Lines")+
        AtomicID::registerId(-1140,"Calibration")+
        AtomicID::registerId(-1168,"Proper")+
        AtomicID::registerId(-1167,"Motion")+
        AtomicID::registerId(-1130,"Sigma")+
        AtomicID::registerId(-1137,"Weight")+
        AtomicID::registerId(-1185,"Origin")+
        AtomicID::registerId(-1116,"Target")+
        AtomicID::registerId(-1192,"Tracking")+
        AtomicID::registerId(-1178,"Beam")+
        AtomicID::registerId(-1146,"Product")+
        AtomicID::registerId(-1184,"Meas")+
        AtomicID::registerId(-1186,"Centroid")+
        AtomicID::registerId(-1125,"AIPSPP")+
        AtomicID::registerId(-1149,"Ignore")+
        AtomicID::registerId(-1151,"VDSID")+
        AtomicID::registerId(-1121,"VisCubeTableFormat")+
        TypeInfoReg::addToRegistry(-1121,TypeInfo(TypeInfo::DYNAMIC,0))+
        DynamicTypeManager::addToRegistry(-1121,__construct_VisCubeTableFormat)+
        AtomicID::registerId(-1157,"VisCubeColumnarTableTile")+
        TypeInfoReg::addToRegistry(-1157,TypeInfo(TypeInfo::DYNAMIC,0))+
        DynamicTypeManager::addToRegistry(-1157,__construct_VisCubeColumnarTableTile)+
        AtomicID::registerId(-1138,"VisCubeVTile")+
        TypeInfoReg::addToRegistry(-1138,TypeInfo(TypeInfo::DYNAMIC,0))+
        DynamicTypeManager::addToRegistry(-1138,__construct_VisCubeVTile)+
        AtomicID::registerId(-1172,"VisCubeVCube")+
        TypeInfoReg::addToRegistry(-1172,TypeInfo(TypeInfo::DYNAMIC,0))+
        DynamicTypeManager::addToRegistry(-1172,__construct_VisCubeVCube)+
        AtomicID::registerId(-1141,"VisCubeVCubeSet")+
        TypeInfoReg::addToRegistry(-1141,TypeInfo(TypeInfo::DYNAMIC,0))+
        DynamicTypeManager::addToRegistry(-1141,__construct_VisCubeVCubeSet)+
    0;
    return res;
  }
  
  int __dum_call_registries_for_VisCube = aidRegistry_VisCube();


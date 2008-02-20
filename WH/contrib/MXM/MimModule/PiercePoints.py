from Timba.TDL import *
from Timba.Meq import meq
from Timba.Contrib.MXM.MimModule.MIM_model import *
import Meow


R_earth=6378135.; # Radius of earth at somewhere.

class PiercePoints(MIM_model):
    """A PiercePoints is a MIM_model that uses pierce points at a given height (default=300km) which can be a (solvable) parameter. get_tec is a function of the calculated piercepoints"""

    def __init__(self,ns,name,sources,stations=None,height=300):
        MIM_model.__init__(self,ns,name,sources,stations);
        if isinstance(height,Meow.Parm): 
            self._height = height;
        else:
            self._height = Meow.Parm(height);

	self.ns.h << self._height .make()
        print "NS:::",self.ns;

        
    def make_rot_matrix(self,ref_station=1):
        ns=self.ns;
        xyz = self.array.xyz();
        #create rotation matrix"
        longlat  = ns['ll'](ref_station);
        rot_matrix = ns['rot'](ref_station);
        if not rot_matrix.initialized():
            if not longlat.initialized():
                longlat << Meq.LongLat(xyz(ref_station));
                lon = ns['lon'](ref_station)<< Meq.Selector(longlat,index=0)
                lat = ns['lat'](ref_station)<< Meq.Selector(longlat,index=1)
                cosl= ns['coslon'](ref_station) <<Meq.Cos(lon); 
                sinl= ns['sinlon'](ref_station) <<Meq.Sin(lon); 
                cosphi= ns['coslat'](ref_station) <<Meq.Cos(lat); 
                sinphi= ns['sinlat'](ref_station) <<Meq.Sin(lat); 
                # create rotation matrix to convert to ENU coordinates
                rot_matrix <<Meq.Composer(-1*sinl,cosl,0,
                                          -1*sinphi*cosl,-1*sinphi*sinl,cosphi,
                                          cosphi*cosl,cosphi*sinl,sinphi,
                                          dims=[3,3]);
        return rot_matrix;

    def make_pp(self,ref_station=None):
        #returns xyz position of pierce point, assumes spherical earth, if elliptical some other method should be chosen. azel seems to be related to spherical earth plus alpha_prime and the last formula calculating the scale.
        ns=self.ns;
        if not ns.earth_radius.initialized():
             ns.earth_radius<< Meq.Constant(R_earth);
        if not ns.pi.initialized():
             ns.pi<< Meq.Constant(math.pi);
             
        xyz = self.array.xyz();
        if ref_station:
            rot_matrix=self.make_rot_matrix(ref_station);
        
                

        for station in self.stations:
            norm_xyz = create_inproduct(ns,xyz(station),xyz(station));
            for src in self.src:
                az = self.get_az()(src,station);
                el = self.get_el()(src,station);
                cos_az = Meq.Cos(az);
                sin_az = Meq.Sin(az);
                cos_el = Meq.Cos(el);
                sin_el = Meq.Sin(el);
                diff = ns['diff'](src,station);
                if  not diff.initialized():
                    diff_vector = diff << Meq.Composer(cos_el*cos_az,
                                                       cos_el*sin_az,
                                                       sin_el);

                    
                    
                    alpha_prime = Meq.Asin(cos_el*norm_xyz/(ns.earth_radius+ns.h*1000.));
                    sec = ns.sec(src,station)<<1./Meq.Cos(alpha_prime);
                    sin_beta = ns.sin_beta(src,station)  << Meq.Sin((0.5*ns.pi - el) - alpha_prime); #angle at center earth
                    scale = ns.scale(src,station)<<(ns.earth_radius+ns.h*1000.)*sin_beta/cos_el;
                    if ref_station:
                        ns['pp'](src,station) << Meq.MatrixMultiply(rot_matrix,xyz(station) + diff_vector*scale);
                    else:
                        ns['pp'](src,station) << xyz(station) + diff_vector*scale;
                        
        return ns['pp'];
                    
        
 
    def make_longlat_pp(self,ref_station=None):
        '''make longitude and lattitude of piercepoints'''
        pp = self.make_xyz_pp(ref_station=ref_station);
        for station in self.stations:
            for src in self.src:                
                x = pp('x',src,station);
                y = pp('y',src,station);
                z = pp('z',src,station);
                pp('lon',src,station) << Meq.Atan(x/y);
                pp('lat',src,station) << Meq.Asin(z/Meq.Sqrt(x*x+y*y+z*z));


    def make_xy_pp(self,ref_station=None):
        '''make xy of piercepoints'''
        pp = self.make_pp(ref_station=ref_station);
        for station in self.stations:
            for src in self.src:
                x = pp('x',src,station);
                y = pp('y',src,station);
                if not x.initialized():
                    x <<Meq.Selector(pp(src,station),index=0);
                if not y.initialized():
                    y <<Meq.Selector(pp(src,station),index=1);
        return pp;

    def make_xyz_pp(self,ref_station=None):
        '''make xyz of piercepoints'''
        pp = self.make_xy_pp(ref_station=ref_station);
        for station in self.stations:
            for src in self.src:
                z = pp('z',src,station);
                if not z.initialized():
                    z <<Meq.Selector(pp(src,station),index=2);


        return pp;

    
def create_inproduct ( ns,a, b,length=0):
    """Computes the dot product of two vectors of arbitrary length""";
    # Definition of dot product: multiply vector elements separately?
    # I.e. A=(a1,a2,a3), B=(b1,b2,b3) ==> A dot B = (a1*b1 + a2*b2 + a3*b3)
    # For now assume that A and B have equal number of elements
    # The Meq.NElements returns a node_stub which is not accepted by the range()
    # so for now only use 3-element vectors.
    # n_elements = ns.Aelements << Meq.NElements(a)
    #we can try to get length from the number of children but this only works if you dotproduct composers...
    if ns.dot(a.name,b.name).initialized():
        return ns.dot(a.name,b.name);
    
    if length ==0 :
        length = a.num_children();
        length_b = b.num_children();
        if length != length_b:
            print "Vectors must be of same length!!!, using smallest"
            length = min(length,length_b);
    sumdot=0
#    print "creating dot product of length",length;
    for i in range(length): # n_elements is a node_stub, cannot be used for loop counts
        if not a('select',i).initialized():
            a('select',i)<<Meq.Selector(a, index=i);
        first = a('select',i);
        if not b('select',i).initialized():
            b('select',i)<<Meq.Selector(b, index=i);
        second = b('select',i);
        sumdot=sumdot+ (first*second)
    dot = ns.dot(a.name,b.name)<<Meq.Sqrt(sumdot)
    return dot
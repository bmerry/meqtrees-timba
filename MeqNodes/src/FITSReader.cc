//# FITSReader.cc: Read a FITS file and return the Result
//#
//# Copyright (C) 2003
//# ASTRON (Netherlands Foundation for Research in Astronomy)
//# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
//#
//# This program is free software; you can redistribute it and/or modify
//# it under the terms of the GNU General Public License as published by
//# the Free Software Foundation; either version 2 of the License, or
//# (at your option) any later version.
//#
//# This program is distributed in the hope that it will be useful,
//# but WITHOUT ANY WARRANTY; without even the implied warranty of
//# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//# GNU General Public License for more details.
//#
//# You should have received a copy of the GNU General Public License
//# along with this program; if not, write to the Free Software
//# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//#
//# $Id$

#include <MeqNodes/FITSReader.h>
#include <MEQ/MeqVocabulary.h>
#include <MEQ/Request.h>
#include <MEQ/Result.h>
#include <MEQ/VellsSlicer.h>
#include <MEQ/AID-Meq.h>
#include <MeqNodes/AID-MeqNodes.h>

//#define DEBUG
extern "C" {
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
// the following is available from the libcfitsio-dev package on Debian,
// in a perfect world it should be found by configure
#include <fitsio.h>
int simple_read_fits_file(const char *filename,  double **myarr,  double ***cells,
				long int *naxis, long int **naxes, int *is_complex);

}/* extern C */

namespace Meq {

const HIID FFilename= AidFilename;


//##ModelId=400E5355029C
FITSReader::FITSReader()
	: Node(0) //no children
{

}

//##ModelId=400E5355029D
FITSReader::~FITSReader()
{}

void FITSReader::setStateImpl (DMI::Record::Ref &rec,bool initializing)
{
	Node::setStateImpl(rec,initializing);

	rec[FFilename].get(filename_,initializing);
#ifdef DEBUG
  cout<<"File Name ="<<filename_<<endl;
#endif

}

 
int FITSReader::getResult (Result::Ref &resref, 
                       const std::vector<Result::Ref> &childres,
                       const Request &request,bool)
{

	double *data;
	double **centers;
	long int naxis, *naxes;
	int is_complex;
  int flag=simple_read_fits_file(filename_.c_str(), &data,  &centers, &naxis, &naxes, &is_complex);

	FailWhen(flag!=0,"Meq::FITSReader file read failed");
#ifdef DEBUG
	cout<<"Read "<<naxis<<" Axes with flag "<<flag<<endl;
	for (int i=0;i<naxis;i++) {
		cout<<i<<": "<<naxes[i]<<",";
	}
	cout<<endl;
#endif
	//create cells
	//
  Domain::Ref domain(new Domain());
  //get the frequency from the request
  const Cells &incells=request.cells();
  const Domain &old_dom=incells.domain();
	for (int i=0;i<naxis;i++) {
			if (naxes[i]) {
			   if (old_dom.isDefined(i)) {
            //domain().defineAxis(i, old_dom.start(i), old_dom.end(i));
            //domain().defineAxis(i, std::min(centers[i][0]-1, old_dom.start(i)),std::max(centers[i][naxes[i]-1]+1, old_dom.end(i)));
            domain().defineAxis(i, centers[i][0]-1,centers[i][naxes[i]-1]+1);
			   } else { //not defined in old domain
            //domain().defineAxis(i, -1e6, 1e6);
            domain().defineAxis(i, centers[i][0]-1,centers[i][naxes[i]-1]+1);
		     }

			}
	}

  Cells::Ref cells_ref;
  Cells &cells=cells_ref<<=new Cells(*domain);

	for (int i=0;i<naxis;i++) {
		if (naxes[i]) {
      blitz::Array<double,1> l_center(centers[i], blitz::shape(naxes[i]), blitz::duplicateData); 
      blitz::Array<double,1> l_space(naxes[i]); 
			//calculate spacings
			for (int j=1; j<naxes[i]-1; j++) {
				l_space(j)=(l_center(j)-l_center(j-1))/2+ (l_center(j+1)-l_center(j))/2;
			}
			if (naxes[i]>1) {
       l_space(0)=l_center(1)-l_center(0);
       l_space(naxes[i]-1)=l_center(naxes[i]-1)-l_center(naxes[i]-2);
			} else {
			 l_space(0)=1;
			}
     //attach to cells
     cells.setCells(i,l_center,l_space);
		}
	}

  // create a result with one VellSet (1), not integrated (0)
  Result &result=resref<<= new Result(1,0); 

	//VellSet
	VellSet::Ref ref0;
	VellSet &vs0=ref0<<=new VellSet(0,1);
	Vells::Shape shape(incells.shape());

	if(shape.size()<(unsigned)naxis) {
		//we need to extend the shape
		shape.resize(naxis,1);//resize and make all 1
	}
  
	for (int i=0;i<naxis;i++) {
		if (naxes[i]) {
			shape[i]=naxes[i];
		} else {
			shape[i]=1;
		}
	}

#ifdef DEBUG
	cout<<"Shape "<<shape<<endl;
#endif
	if (!is_complex) {
	if (naxis==0) {
	  // scalar
	  vs0.setValue(new Vells(*data));
	} else { 
	vs0.setShape(shape);
	Vells &out=vs0.setValue(new Vells(0.0,shape));
	if (naxis==1) {
	  blitz::Array<double,1> A(data,shape,blitz::duplicateData);
		VellsSlicer<double,1> slout(out,0);
		slout=A;
	}else if (naxis==2) {
	  blitz::Array<double,2> A(data,shape,blitz::duplicateData);
		VellsSlicer<double,2> slout(out,0,1);
		slout=A;
	}else if (naxis==3) {
	  blitz::Array<double,3> A(data,shape,blitz::duplicateData);
		VellsSlicer<double,3> slout(out,0,1,2);
		slout=A;
	}else if (naxis==4) {
	  blitz::Array<double,4> A(data,shape,blitz::duplicateData);
		VellsSlicer<double,4> slout(out,0,1,2,3);
		slout=A;
	}
	}
	} else { //we have complex data
		dcomplex *cdata=reinterpret_cast<dcomplex *>(data);

  	if (naxis==0) {
	    // scalar
	    vs0.setValue(new Vells(*cdata));
	   } else { 
	    vs0.setShape(shape);
	    Vells &out=vs0.setValue(new Vells((dcomplex)0.0,shape));
	    if (naxis==1) {
	     blitz::Array<dcomplex,1> A(cdata,shape,blitz::duplicateData);
		   VellsSlicer<dcomplex,1> slout(out,0);
		   slout=A;
	   }else if (naxis==2) {
	     blitz::Array<dcomplex,2> A(cdata,shape,blitz::duplicateData);
		   VellsSlicer<dcomplex,2> slout(out,0,1);
		   slout=A;
	   }else if (naxis==3) {
	     blitz::Array<dcomplex,3> A(cdata,shape,blitz::duplicateData);
		   VellsSlicer<dcomplex,3> slout(out,0,1,2);
		   slout=A;
	   }else if (naxis==4) {
	     blitz::Array<dcomplex,4> A(cdata,shape,blitz::duplicateData);
		   VellsSlicer<dcomplex,4> slout(out,0,1,2,3);
		   slout=A;
	   }
	 }
	}
	result.setVellSet(0,ref0);
	if (naxis) {
	 result.setCells(cells);
	}

	for (long int ii=0; ii<naxis; ii++) {
		free(centers[ii]);
	}
	if (naxis) {
	 free(naxes);
	 free(centers);
	}
	free(data);
 return flag;
}


} // namespace Meq
int simple_read_fits_file(const char *filename,  double **arr,  double ***cells,
			long int *naxis, long int **naxes, int *is_complex) {

       fitsfile *fptr;
			 int status;

			 long int  nelements;
			 int datatype=0;
			 long int ii,jj;

			 int bitpix;
			 long int *increment, *fpix, *lpix;

			 long int firstrow,firstelem;
			 long int nrows;
			 int  ncols,hdunum,hdutype;
			 int null_flag=0;
			 int anynulls=0;
			 int stat;

			 long int *mynaxes;
			 int mynaxis=0;
			 double *colarr=0;
			 int has_cells;

			 status=0;
			 stat=fits_open_file(&fptr, filename, READONLY, &status);
       if(stat!=0) return -1;


			 fits_get_img_dim(fptr,&mynaxis,&status);

			 if ((mynaxes=(long int*)calloc((size_t)mynaxis,sizeof(long int)))==0) {
			   fprintf(stderr,"no free memory\n");
				 exit(1);
			 }
			 /* the following arrays are needed to read in the image */
			 if ((increment=(long int*)calloc((size_t)mynaxis,sizeof(long int)))==0) {
			   fprintf(stderr,"no free memory\n");
				 exit(1);
			 }
			 if ((fpix=(long int*)calloc((size_t)mynaxis,sizeof(long int)))==0) {
			   fprintf(stderr,"no free memory\n");
				 exit(1);
			 }
			 if ((lpix=(long int*)calloc((size_t)mynaxis,sizeof(long int)))==0) {
			   fprintf(stderr,"no free memory\n");
				 exit(1);
			 }

			 fits_get_img_size(fptr,mynaxis, mynaxes, &status);
#ifdef DEBUG
			 printf("image has %d axes\n",mynaxis);
			 for (ii=0; ii<mynaxis; ii++)
				 printf("%ld ( %ld ) ",ii,mynaxes[ii]);
			 printf("\n");
#endif
       fits_get_img_type(fptr,&bitpix,&status);
			 if (bitpix!=DOUBLE_IMG)
					printf("wrong data type\n");

			 switch (bitpix) {
				case BYTE_IMG:
					datatype=TBYTE;
					break;
				case SHORT_IMG:
					datatype=TSHORT;
					break;
				case LONG_IMG:
					datatype=TLONG;
					break;
				case FLOAT_IMG:
					datatype=TFLOAT;
					break;
				case DOUBLE_IMG:
					datatype=TDOUBLE;
					break;

			  default:
			    break;		
			 }

			 nelements=1;
			 for (ii=0; ii<mynaxis; ii++) {
				if (mynaxes[ii]) {
				 nelements*=mynaxes[ii];
				 increment[ii]=1;
				 fpix[ii]=1;
				 lpix[ii]=mynaxes[ii];
				}else{
				 increment[ii]=0;
				 fpix[ii]=0;
				 lpix[ii]=mynaxes[ii];
				}
       }

			 /* allocate array for data */
			 if ((*arr=(double*)calloc((size_t)nelements,sizeof(double)))==0) {
				fprintf(stderr,"no free memory\n");
				exit(1);
			 }
			 /* read the whole image increment=[1,1,1,..]*/
			 fits_read_subset(fptr, datatype, fpix, lpix, increment,
													    0, *arr, &null_flag, &status);

#ifdef DEBUG
			 for (ii=0;ii<nelements;ii++) {
					printf("%ld: %lf ",ii,(*arr)[ii]);
			 }
			 printf("\n");
#endif
			 /* read the hader key to see if data is complex */
			 fits_read_key(fptr,TINT,"CPLEX",is_complex,NULL,&status);
			 if (status==KEY_NO_EXIST) {
					*is_complex=0;
					status=0;
			 }


			 /* read the hader key to see if cells are present */
			 fits_read_key(fptr,TINT,"CELLS",&has_cells,NULL,&status);
			 if (status==KEY_NO_EXIST) {
					/* no cells ! */
					has_cells=0;
					status=0;
			 }
#ifdef DEBUG
			 printf("cells present=%d\n",has_cells);
#endif

			 if (has_cells) {
			 /* the table */
			 if ( fits_get_hdu_num(fptr, &hdunum) == 1 ) {
			  /* This is the primary array;  try to move to the */
			  /* first extension and see if it is a table */
			  fits_movabs_hdu(fptr, 2, &hdutype, &status);
			 } else {
					printf("no table found\n");
					status=-1;
			 }

			 if (hdutype != BINARY_TBL)  {
				printf("Error: expected to find a binary table in this HDU\n");
				status=-1;
			 }

			 fits_get_num_rows(fptr,&nrows,&status);
			 fits_get_num_cols(fptr,&ncols,&status);


#ifdef DEBUG
			 printf("table cols=%d (expected=%d), rows=%ld\n",ncols,mynaxis,nrows);
#endif
			 *naxis=ncols; /* the true number of axes  */
       /* cells of each axes (centers) */
	  	 if ((*cells=(double**)calloc((size_t)ncols,sizeof(double*)))==0) {
				fprintf(stderr,"no free memory\n");
				exit(1);
			 }
			 /* storage for each column */
			 if ((colarr=(double*)calloc((size_t)(nrows),sizeof(double)))==0) {
				fprintf(stderr,"no free memory\n");
				exit(1);
			 }

			 if ((*naxes=(long int*)calloc((size_t)ncols,sizeof(long int)))==0) {
			   fprintf(stderr,"no free memory\n");
				 exit(1);
			 }

			 firstrow=1;
			 firstelem=1;
			 /* read each column */
			 for (ii=0; ii<ncols; ii++) {
				memset(colarr,0,sizeof(double)*(size_t)(nrows));
    		fits_read_col(fptr, TDOUBLE, ii+1, firstrow, firstelem, nrows,
														&null_flag, colarr, &anynulls, &status);

				(*naxes)[ii]=(long int)colarr[0];
				if ((*naxes)[ii]) {
	  	   if (((*cells)[ii]=(double*)calloc((size_t)(*naxes)[ii],sizeof(double)))==0) {
				  fprintf(stderr,"no free memory\n");
				  exit(1);
			   }
					memcpy((*cells)[ii],&colarr[1],sizeof(double)*((size_t)((*naxes)[ii])));
				}
			 }


#ifdef DEBUG
			 for (ii=0; ii<*naxis; ii++) {
				printf("axis %ld\n",ii);
	  		 for (jj=0; jj<(*naxes)[ii];jj++) 
		   			printf(" %lf, ",(*cells)[ii][jj]);
				 printf("\n");

			 }
#endif

			 } else {
				 /* no cells present, a scalar */
				*naxis=0;
			 }
			 fits_close_file(fptr,&status);


			 fits_report_error(stderr, status);

  		 free(mynaxes);

			 free(increment);
			 free(fpix);
			 free(lpix);

			 if (has_cells) 
			  free(colarr);


			return 0;
}

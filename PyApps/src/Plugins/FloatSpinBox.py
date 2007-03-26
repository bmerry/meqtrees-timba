# floatspinbox.py: Class to create a Qt SpinBox with floating point numbers

#
# Copyright (C) 2007
# ASTRON (Netherlands Foundation for Research in Astronomy)
# and The MeqTree Foundation
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Acknowledgement: This code is directly taken from the example
# posted by Joerg Ott to the Trolltech QT Interest mailing list on
# 26 August 1998
#
# This is a python translation of the ACSIS 'floatspinbox' C++ code 
#
# Acknowledgement: This code is adapted from the example
# posted by Joerg Ott to the Trolltech QT Interest mailing list on
# 26 August 1998
#


import sys
from qt import *
#from math import round
from math import pow

def QMAX( x, y ):
  if y > x:
    return y
  return x

class FloatSpinBox(QSpinBox):

  def __init__( self, minValue=0.0,maxValue=1.0,decimals=1,step=0.1,parent=None,name=None ):
    QSpinBox.__init__(self,int(minValue*pow(10,decimals)), int(maxValue*pow(10,decimals)), \
	      int(round(step * pow(10,decimals))), parent, name )
    self.dec = decimals
    self.dVal = QDoubleValidator(float(minValue), float(maxValue), self.dec, self, "dVal")
    self.setValidator(self.dVal);	
    self.setValue( 0 );
    self.setWrapping(True)


  def mapValueToText (self, value):
    s = QString()
    s.setNum( float(value)/ pow(10,self.dec), 'f', self.dec )
    return s

  def mapTextToValue (ok=True):
    return int( self.cleanText().toFloat(ok)*pow(10,self.dec))

  def value(self):
    return float(QRangeControl.value(self))/pow(10,self.dec)

  def minValue(self):
    return float(QRangeControl.minValue(self))/pow(10,self.dec)

  def maxValue(self):
    return float(QRangeControl.maxValue(self))/pow(10,self.dec)

  def setFloatValue(self, value):
    QRangeControl.setValue(self,int(value* pow(10,self.dec)))


  def setRange(self, minValue, maxValue):
    QRangeControl.setRange(self, int( minValue *  pow( 10, self.dec ) ),  \
			   int( maxValue *  pow( 10, self.dec ) ) )
    self.dVal.setRange( float(minValue), float(maxValue), 2 )

  def valueChange(self):
    QSpinBox.valueChange(self)
#   self.emit(SIGNAL("valueChanged(value())"),self.value())
    self.emit(SIGNAL("valueChanged(float)"),(self.value(),))

  def sizeHint(self):
    fm = QFontMetrics(self.fontMetrics())
    h = int(fm.height())
    if ( h < 12 ):      # ensure enough space for the button pixmaps
        h = 12 
    w = 35          # minimum width for the value
    wx = int(fm.width( "  " )) 
    s = QString()
    s.setNum( self.minValue(), 'f', self.dec ) 
    s.prepend( self.prefix() ) 
    s.append( self.suffix() ) 
    w = QMAX( w, fm.width( s ) + wx ) 
    s.setNum( self.maxValue(), 'f', self.dec ) 
    s.prepend( self.prefix() ) 
    s.append( self.suffix() ) 
    w = QMAX( w, fm.width( s ) + wx ) 
    s = self.specialValueText() 
    w = QMAX( w, fm.width( s ) + wx ) 

    r = QSize( h    # buttons AND frame both sides
             + 6  # right/left margins
             + w, # widest value
#             frameWidth() * 2 // top/bottom frame
	     h
             + 4  # top/bottom margins
             + h  # font height
             )
    return r;



def main(args):
    app = QApplication(args)
#   demo = FloatSpinBox(parent=None)
    demo = FloatSpinBox(5.0,20.2,2,0.1,parent=None)
    demo.show()
    app.setMainWidget(demo)
    app.exec_loop()


# Admire
if __name__ == '__main__':
    main(sys.argv)

#!/usr/bin/env python

# Contributed by Tomaz Curk in a bug report showing that the stack order of the
# curves was dependent on the number of curves. This has been fixed in Qwt.
#
# QwtBarCurve is an idea of Tomaz Curk.
#
# Beautified and expanded by Gerard Vermeulen.

import math
import random
import sys
from qt import *
from qwt import *
from numarray import *
from app_pixmaps import pixmaps

from math import sin
from math import cos
from math import pow
from math import sqrt

# local python Error Bar class
from ErrorBar import *

from dmitypes import verbosity
_dbg = verbosity(0,name='realvsimag');
_dprint = _dbg.dprint;
_dprintf = _dbg.dprintf;

# Note: using _dprintf (from Oleg)
#The function call is _dprint(N,...), where N is the "debug level". 
#This is a conditional debug-print function; 
#you enable debug-printing via the command line, e.g.:
                                                                                
# ./meqbrowser.py -drealvsimag=5
                                                                                
#which causes all _dprint() statements with N<=5 to execute (and keeps
#the screen clutter-free otherwise). Please try to use _dprint() for all
#your diagnostic printing, as this scheme keeps diagnostic messages clean
#(i.e. I don't see yours unless I enable them, and so they don't get in
#the way of mine).

class PrintFilter(QwtPlotPrintFilter):
    def __init__(self):
        QwtPlotPrintFilter.__init__(self)

    # __init___()
    
    def color(self, c, item, i):
        if not (self.options() & QwtPlotPrintFilter.PrintCanvasBackground):
            if item == QwtPlotPrintFilter.MajorGrid:
                return Qt.darkGray
            elif item == QwtPlotPrintFilter.MinorGrid:
                return Qt.gray
        if item == QwtPlotPrintFilter.Title:
            return Qt.red
        elif item == QwtPlotPrintFilter.AxisScale:
            return Qt.green
        elif item == QwtPlotPrintFilter.AxisTitle:
            return Qt.blue
        return c

    # color()

    def font(self, f, item, i):
        result = QFont(f)
        result.setPointSize(int(f.pointSize()*1.25))
        return result

    # font()

# class PrintFilter

class realvsimag_plotter(object):

    color_table = {
        'none': None,
        'black': Qt.black,
        'blue': Qt.blue,
        'cyan': Qt.cyan,
        'gray': Qt.gray,
        'green': Qt.green,
        'magenta': Qt.magenta,
        'red': Qt.red,
        'white': Qt.white,
        'yellow': Qt.yellow,
        'darkBlue' : Qt.darkBlue,
        'darkCyan' : Qt.darkCyan,
        'darkGray' : Qt.darkGray,
        'darkGreen' : Qt.darkGreen,
        'darkMagenta' : Qt.darkMagenta,
        'darkRed' : Qt.darkRed,
        'darkYellow' : Qt.darkYellow,
        'lightGray' : Qt.lightGray,
        }

    symbol_table = {
        'none': QwtSymbol.None,
        'rectangle': QwtSymbol.Rect,
        'ellipse': QwtSymbol.Ellipse,
        'circle': QwtSymbol.Ellipse,
	'xcross': QwtSymbol.XCross,
	'cross': QwtSymbol.Cross,
	'triangle': QwtSymbol.Triangle,
	'diamond': QwtSymbol.Diamond,
        }

    line_style_table = {
        'none': QwtCurve.NoCurve,
        'lines' : QwtCurve.Lines,
        'steps' : QwtCurve.Steps,
        'stick' : QwtCurve.Sticks,
        'dots' : QwtCurve.Dots,
#        'none': Qt.NoPen,
        'SolidLine' : Qt.SolidLine,
        'DashLine' : Qt.DashLine,
        'DotLine' : Qt.DotLine,
        'DashDotLine' : Qt.DashDotLine,
        'DashDotDotLine' : Qt.DashDotDotLine,
        'solidline' : Qt.SolidLine,
        'dashline' : Qt.DashLine,
        'dotline' : Qt.DotLine,
        'dashdotline' : Qt.DashDotLine,
        'dashdotdotline' : Qt.DashDotDotLine,
        }

    
    def __init__(self, plot_key=None, parent=None):
        # QWidget.__init__(self, parent)

        self.plot_key = plot_key

        # Initialize a QwPlot central widget
        self.plot = QwtPlot('', parent)
        self.plot.plotLayout().setCanvasMargin(0)
          
# for legend ...
#        self.plot.setAutoLegend(True)
#        self.plot.enableLegend(True)
#        self.plot.setLegendPos(Qwt.Bottom)
#        self.plot.setLegendFrameStyle(QFrame.Box | QFrame.Sunken)

        self._mainwin = parent and parent.topLevelWidget();
        # get status bar
        self._statusbar = self._mainwin and self._mainwin.statusBar();

        self.__initTracking()
        self.__initZooming()
        # forget the toolbar for now -- too much trouble when we're dealing with 
        # multiple windows. Do a context menu instead
        # self.__initToolBar()
        self.__initContextMenu()

        # initialize internal variables for plot
        self._circle_dict = {}
        self._line_dict = {}
        self._xy_plot_dict = {}
        self._xy_plot_color = {}
        self._plotter_dict = {}
        self._plotterlabels_dict = {}
        self._plotterlabels_start = {}
        self._x_errors_dict = {}
        self._y_errors_dict = {}

        self.plot_mean_circles = False
        self.plot_stddev_circles = False
        self.plot_mean_arrows = False
        self.plot_symbol = None
        self.plot_symbol_size = None
        self.plot_line_style = None
        self._plot_title = None
        self._legend_plot = None
        self._legend_popup = None

        self.plot.setAxisTitle(QwtPlot.xBottom, 'Real Axis')
        self.plot.setAxisTitle(QwtPlot.yLeft, 'Imaginary Axis')
        self.index = -1
        self._angle = 0.0
        self._radius = 20.0

# used for plotting MeqParm solutions
        self.x_list = []
        self.y_list = []
        self.value = 100

# used for errors plotting 
        self.errors_plot = False
# used for errors plot testing 
        self.gain = 1.0

    def reset_data_collectors(self):
        self._plotter_dict = {}

    # __init__()

    def set_compute_circles (self, do_compute_circles=True):
        self.plot_mean_circles = do_compute_circles



    def __initTracking(self):
        """Initialize tracking
        """        
        QObject.connect(self.plot,
                     SIGNAL('plotMouseMoved(const QMouseEvent&)'),
                     self.onMouseMoved)
        QObject.connect(self.plot, SIGNAL("plotMousePressed(const QMouseEvent&)"),
                        self.slotMousePressed)

        self.plot.canvas().setMouseTracking(True)
        if self._statusbar:
          self._statusbar.message(
            'Plot cursor movements are tracked in the status bar',2000)

    # __initTracking()

    def onMouseMoved(self, e):
        if self._statusbar:
          self._statusbar.message(
            'x = %+.6g, y = %.6g'
            % (self.plot.invTransform(QwtPlot.xBottom, e.pos().x()),
               self.plot.invTransform(QwtPlot.yLeft, e.pos().y())),2000)

    # onMouseMoved()
    
    def __initZooming(self):
        """Initialize zooming
        """
        self.zoomer = QwtPlotZoomer(QwtPlot.xBottom,
                                    QwtPlot.yLeft,
                                    QwtPicker.DragSelection,
                                    QwtPicker.AlwaysOff,
                                    self.plot.canvas())
        self.zoomer.setRubberBandPen(QPen(Qt.black))

        self.picker = QwtPlotPicker(
            QwtPlot.xBottom,
            QwtPlot.yLeft,
            QwtPicker.PointSelection | QwtPicker.DragSelection,
            QwtPlotPicker.CrossRubberBand,
            QwtPicker.AlwaysOn,
            self.plot.canvas())
        self.picker.setRubberBandPen(QPen(Qt.green))
        QObject.connect(self.picker, SIGNAL('selected(const QPointArray &)'),
                     self.selected)



    # __initZooming()
       
    def setZoomerMousePattern(self, index):
        """Set the mouse zoomer pattern.
        """
        if index == 0:
            pattern = [
                QwtEventPattern.MousePattern(Qt.LeftButton, Qt.NoButton),
                QwtEventPattern.MousePattern(Qt.RightButton, Qt.NoButton),
#                QwtEventPattern.MousePattern(Qt.MidButton, Qt.NoButton),
                QwtEventPattern.MousePattern(Qt.LeftButton, Qt.ShiftButton),
                QwtEventPattern.MousePattern(Qt.RightButton, Qt.ShiftButton),
#                QwtEventPattern.MousePattern(Qt.MidButton, Qt.ShiftButton),
                ]
            self.zoomer.setMousePattern(pattern)
        elif index in (1, 2, 3):
            self.zoomer.initMousePattern(index)
        else:
            raise ValueError, 'index must be in (0, 1, 2, 3)'

    # setZoomerMousePattern()
    def __initContextMenu(self):
        """Initialize the toolbar
        """
        # skip if no main window
        if not self._mainwin:
          return;
          
        self._menu = QPopupMenu(self._mainwin);
        
        zoom = QAction(self.plot);
        zoom.setIconSet(pixmaps.viewmag.iconset());
        zoom.setText("Enable zoomer");
        zoom.setToggleAction(True);
        # zoom.setAccel() can set keyboard accelerator
        QObject.connect(zoom,SIGNAL("toggled(bool)"),self.zoom);
        zoom.addTo(self._menu);
        
        printer = QAction(self.plot);
        printer.setIconSet(pixmaps.fileprint.iconset());
        printer.setText("Print plot");
        QObject.connect(printer,SIGNAL("activated()"),self.printPlot);
        printer.addTo(self._menu);
        
        self.zoom(False);
        self.setZoomerMousePattern(0);

##    def __initToolBar(self):
##        """Initialize the toolbar
##        """
##        # skip if no main window
##        if not self._mainwin:
##          return;
##        if not self.toolBar:
##          self.toolBar = QToolBar(self._mainwin);
##
##          self.__class__.btnZoom = btnZoom = QToolButton(self.toolBar)
##          btnZoom.setTextLabel("Zoom")
##          btnZoom.setPixmap(QPixmap(zoom_xpm))
##          btnZoom.setToggleButton(True)
##          btnZoom.setUsesTextLabel(True)
##
##          self.__class__.btnPrint = btnPrint = QToolButton(self.toolBar)
##          btnPrint.setTextLabel("Print")
##          btnPrint.setPixmap(QPixmap(print_xpm))
##          btnPrint.setUsesTextLabel(True)
##
##          QWhatsThis.whatsThisButton(self.toolBar)
##
##          QWhatsThis.add(
##              self.plot.canvas(),
##              'A QwtPlotZoomer lets you zoom infinitely deep\n'
##              'by saving the zoom states on a stack.\n\n'
##              'You can:\n'
##              '- select a zoom region\n'
##              '- unzoom all\n'
##              '- walk down the stack\n'
##              '- walk up the stack.\n\n'
##              )
##        
##        self.zoom(False)
##
##        self.setZoomerMousePattern(0)
##
##        QObject.connect(self.btnPrint, SIGNAL('clicked()'),
##                     self.printPlot)
##        QObject.connect(self.btnZoom, SIGNAL('toggled(bool)'),
##                     self.zoom)

    # __initToolBar()

    def slotMousePressed(self, e):
        "Mouse press processing instructions go here"
        _dprint(2,' in slotMousePressed');
        _dprint(3,' slotMousePressed event:',e);
        if e.button() == QMouseEvent.MidButton:
            _dprint(2,'button is mid button');
            xPos = e.pos().x()
            yPos = e.pos().y()
            _dprint(2,'xPos yPos ', xPos, ' ', yPos);
# get curve number associated with this data point
            key, distance, xVal, yVal, index = self.plot.closestCurve(xPos, yPos)
            _dprint(2,' key, distance, xVal, yVal, index ', key, ' ', distance,' ', xVal, ' ', yVal, ' ', index);
# determine the data source for the given curve or point
            message = ''
            message1 = ''
            plot_keys = self._xy_plot_dict.keys()
            _dprint(2, 'plot_keys ', plot_keys)
            for i in range(0, len(plot_keys)):
              current_plot_key = plot_keys[i]
              plot_key = self._xy_plot_dict[current_plot_key]
              if plot_key == key:
                data_key_r = current_plot_key + '_r'
                label = self._plotterlabels_dict[data_key_r]
                start_pos =  self._plotterlabels_start[data_key_r]
                label_index = None
                for j in range(0, len(start_pos)):
                  if index == start_pos[j]:
                    label_index = j
                    break
                  if index > start_pos[j]:
                    continue
                  else:
                    label_index = j - 1
                    break 
                if label_index is None:
                  label_index = len(start_pos) - 1
                _dprint(2, 'label ', label)
                message = 'this point comes from ' + label[label_index] 
                message1 = 'this point comes from \n ' + label[label_index] 
                _dprint(2,message)
                break

# alias
            fn = self.plot.fontInfo().family()

# text marker giving source of point that was clicked
            m = self.plot.insertMarker()
            ylb = self.plot.axisScale(QwtPlot.yLeft).lBound()
            xlb = self.plot.axisScale(QwtPlot.xBottom).lBound()
            self.plot.setMarkerPos(m, xlb, ylb)
            self.plot.setMarkerLabelAlign(m, Qt.AlignRight | Qt.AlignTop)
            self.plot.setMarkerLabel( m, message1,
              QFont(fn, 12, QFont.Bold, False),
              Qt.blue, QPen(Qt.red, 2), QBrush(Qt.yellow))
            self.plot.replot()
            timer = QTimer(self.plot)
            timer.connect(timer, SIGNAL('timeout()'), self.timerEvent_marker)
            timer.start(3000, True)

        elif e.button() == QMouseEvent.RightButton:
          e.accept();  # accept even so that parent widget won't get it
          # popup the menu
          self._menu.popup(e.globalPos());
            
    # slotMousePressed

    def timerEvent_marker(self):
      self.plot.removeMarkers()
      self.plot.replot()
    # timerEvent_marker()

# compute points for two circles
    def compute_circles (self, item_tag, radius, x_cen=0.0, y_cen=0.0):
      """ compute values for circle running through specified
          point and a line pointing to the point """

      # compute circle that will run through average value
      x_pos = zeros((73,),Float64)
      y_pos = zeros((73,),Float64)
      angle = -5.0
      for j in range(0, 73 ) :
        angle = angle + 5.0
        x_pos[j] = x_cen + radius * cos(angle/57.2957795)
        y_pos[j] = y_cen + radius * sin(angle/57.2957795)

      # if this is a new item_tag, add a new circle,
      # otherwise, replace old one
      circle_key = item_tag + '_circle'
      if self._circle_dict.has_key(circle_key) == False: 
        key_circle = self.plot.insertCurve(circle_key)
        self._circle_dict[circle_key] = key_circle
        self.plot.setCurvePen(key_circle, QPen(self._plot_color))
        self.plot.setCurveData(key_circle, x_pos, y_pos)
      else:
        key_circle = self._circle_dict[circle_key] 
        self.plot.setCurveData(key_circle, x_pos, y_pos)

    def compute_arrow (self, item_tag,avg_r, avg_i, x_cen=0.0, y_cen=0.0):
      """ compute values for circle running through specified
          point and a line pointing to the point """

      # compute line that will go from centre of circle to 
      # position of average value
      x1_pos = zeros((2,),Float64)
      y1_pos = zeros((2,),Float64)
      x1_pos[0] = x_cen
      y1_pos[0] = y_cen
      x1_pos[1] = avg_r
      y1_pos[1] = avg_i

      # if this is a new item_tag, add a new arrow,
      # otherwise, replace old one
      line_key = item_tag + '_arrow'
      if self._line_dict.has_key(line_key) == False: 
        key_line = self.plot.insertCurve(line_key)
        self._line_dict[line_key] = key_line
        self.plot.setCurvePen(key_line, QPen(self._plot_color))
        self.plot.setCurveData(key_line, x1_pos, y1_pos)
      else:
        key_line = self._line_dict[line_key]
        self.plot.setCurveData(key_line, x1_pos, y1_pos)

    def plot_data(self, visu_record, attribute_list=None):
      """ process incoming data and attributes into the
          appropriate type of plot """
      _dprint(2,'****** in plot_data');

      self.plot_mean_circles = False
      self.plot_stddev_circles = False
      self.plot_mean_arrows = False
      self.plot_symbol = None
      self.plot_symbol_size = None
      self.plot_line_style = None
      self._plot_title = None
      self._legend_plot = None
      self._legend_popup = None
      self.value_tag = None
      self.error_tag = None
      self._plot_x_axis_label = None
      self._plot_y_axis_label = None
      self._plot_color = None
      self._string_tag = None
      self._tag = None
      self._tag_plot_attrib={}


# first find out what kind of plot we are making
      self._plot_type = None
      item_tag = ''
      if attribute_list is None and visu_record.has_key('attrib'):
        self._attrib_parms = visu_record['attrib']
        _dprint(2,'self._attrib_parms ', self._attrib_parms);
        self._plot_parms = self._attrib_parms.get('plot')
        if self._plot_parms.has_key('tag_attrib'):
          temp_parms = self._plot_parms.get('tag_attrib')
          tag = temp_parms.get('tag')
          self._tag_plot_attrib[tag] = temp_parms
        if self._plot_parms.has_key('attrib'):
          temp_parms = self._plot_parms.get('attrib')
          self._plot_parms = temp_parms
        self._plot_type = self._plot_parms.get('plot_type', 'realvsimag')
        self.plot_mean_circles = self._plot_parms.get('mean_circle', False)
        self.plot_stddev_circles = self._plot_parms.get('stddev_circle', False)
        self.plot_mean_arrows = self._plot_parms.get('mean_arrow', False)
        self.plot_symbol_size = self._plot_parms.get('symbol_size', 10)
        self.plot_symbol = self._plot_parms.get('symbol', 'circle')
        self.plot_line_style = self._plot_parms.get('line_style', 'dots')
        self.value_tag = self._plot_parms.get('value_tag', False)
        self.error_tag = self._plot_parms.get('error_tag', False)
        self._tag = self._attrib_parms.get('tag','') 
        if isinstance(self._tag, tuple):
          for i in range(0, len(self._tag)):
            temp_key = item_tag + self._tag[i]
            item_tag = temp_key
          temp_key = item_tag
          self._string_tag = temp_key 
          item_tag = temp_key + '_plot'
        else:
          self._string_tag = self._tag 
          item_tag = self._tag + '_plot'
      else:
        list_length = len(attribute_list)

# first, get tag at point closest to leaf
#        self._attrib_parms = attribute_list[list_length-1]
#        _dprint(2,'self._attrib_parms ', self._attrib_parms);
#        self._tag = self._attrib_parms.get('tag','') 
#        item_tag = self._tag + '_plot'

# propagate down from root to leaves filling in attributes as soon
# as they are detected
        for i in range(list_length):
          self._attrib_parms = attribute_list[i]
          _dprint(2,'self._attrib_parms ', self._attrib_parms);
          if self._tag is None and self._attrib_parms.has_key('tag'):
            self._tag = self._attrib_parms.get('tag')
            if isinstance(self._tag, tuple):
              for i in range(0, len(self._tag)):
                temp_key = item_tag + self._tag[i]
                item_tag = temp_key
              temp_key = item_tag
              self._string_tag = temp_key 
              item_tag = temp_key + '_plot'
            else:
              self._string_tag = self._tag 
              item_tag = self._tag + '_plot'
          if self._attrib_parms.has_key('plot'):
            self._plot_parms = self._attrib_parms.get('plot')
            if self._plot_parms.has_key('tag_attrib'):
              temp_parms = self._plot_parms.get('tag_attrib')
              tag = temp_parms.get('tag')
              self._tag_plot_attrib[tag] = temp_parms
            if self._plot_parms.has_key('attrib'):
              temp_parms = self._plot_parms.get('attrib')
              self._plot_parms = temp_parms
            _dprint(2,'self._plot_parms ', self._plot_parms);
            if self._plot_type is None and self._plot_parms.has_key('plot_type'):
              self._plot_type = self._plot_parms.get('plot_type')
            _dprint(2,'self._plot_x_axis_label ', self._plot_x_axis_label);
            _dprint(2,'self._plot_parms ', self._plot_parms);
            _dprint(2,'self._plot_parms.has_key(x_axis) ', self._plot_parms.has_key('x_axis'));
            if self._plot_x_axis_label is None and self._plot_parms.has_key('x_axis'):
              self._plot_x_axis_label = self._plot_parms.get('x_axis')
            if self._plot_y_axis_label is None and self._plot_parms.has_key('y_axis'):
              self._plot_y_axis_label = self._plot_parms.get('y_axis')
            if self._plot_title is None and self._plot_parms.has_key('title'):
              self._plot_title = self._plot_parms.get('title')
            if self.value_tag is None and self._plot_parms.has_key('value_tag'):
              self.value_tag = self._plot_parms.get('value_tag')
            if self.error_tag is None and self._plot_parms.has_key('error_tag'):
              self.error_tag = self._plot_parms.get('error_tag')

            if not self.plot_mean_circles and self._plot_parms.has_key('mean_circle'):
              self.plot_mean_circles = self._plot_parms.get('mean_circle')
            if not self.plot_stddev_circles and self._plot_parms.has_key('stddev_circle'):
              self.plot_stddev_circles = self._plot_parms.get('stddev_circle')
            if not self.plot_mean_arrows and self._plot_parms.has_key('mean_arrow'):
              self.plot_mean_arrows = self._plot_parms.get('mean_arrow')
            if self.plot_symbol_size is None and self._plot_parms.has_key('symbol_size'):
              self.plot_symbol_size = int(self._plot_parms.get('symbol_size'))
              _dprint(3, 'plot sysmbol size set to ', self.plot_symbol_size)
            if self.plot_symbol is None and self._plot_parms.has_key('symbol'):
              self.plot_symbol = self._plot_parms.get('symbol')
            if self.plot_line_style is None and self._plot_parms.has_key('line_style'):
              self.plot_line_style = self._plot_parms.get('line_style')
            if self._plot_color is None and self._plot_parms.has_key('color'):
              self._plot_color = self._plot_parms.get('color')
              _dprint(3, 'plot color set to ', self._plot_color)
              self._plot_color = self.color_table[self._plot_color]

      if len(self._tag_plot_attrib) > 0:
        _dprint(3, 'self._tag_plot_attrib has keys ', self._tag_plot_attrib.keys())
# if still undefined
      if self._tag is None:
            self._tag = 'data'
            item_tag = self._tag + '_plot'
      if self._plot_title is None:
        self._plot_title = self._plot_type
      if self.value_tag is None:
        self.value_tag = False
        self.errors_plot = False
      if self.error_tag is None:
        self.error_tag = False
        self.errors_plot = False
      else:
        if not self.value_tag == False:
          _dprint(2, 'errors plot is true')
          self.errors_plot = True

      if self.plot_symbol_size is None:
        self.plot_symbol_size = 10
      if self.plot_symbol is None:
        self.plot_symbol = 'circle'
      if self.plot_line_style is None:
        self.plot_line_style = 'dots'
      if self._plot_color is None:
        self._plot_color = 'blue'
        self._plot_color = self.color_table[self._plot_color]


# extract and define labels for this data item
      self._label_i = item_tag + "_i"
      self._label_r = item_tag + "_r"

      if visu_record.has_key('value'):
        self._data_values = visu_record['value']
#        _dprint(2,'self._data_values ', self._data_values);
      if visu_record.has_key('label'):
        self._data_labels = visu_record['label']
        _dprint(2,'self._data_labels ', self._data_labels);

     # now generate plot 
      self.x_vs_y_plot(item_tag)
  
    def x_vs_y_plot (self,item_tag):
      """ plot real vs imaginary values together with circles
          indicating average values """
 
# get and combine all plot array data together into one array
      num_plot_arrays = len(self._data_values)
      _dprint(2,' num_plot_arrays ', num_plot_arrays);
      self._is_complex = True;
      data_r = []
      data_i = []
      start_pos = []
      sum_r = 0.0
      sum_i = 0.0
      for i in range(0, num_plot_arrays):
# make sure we are using a numarray
        array_representation = inputarray(self._data_values[i])
        xx_r = None
        xx_i = None
        if i == 0:
          start_pos.append(0)
        else:
          start_pos.append(len(data_r))
        if array_representation.type() == Complex64:
          _dprint(2,'array is complex')
          xx_r = array_representation.getreal()
          xx_i = array_representation.getimag()
        else:
          xx_r = array_representation
          self._is_complex = False
          _dprint(2,'array is real')
        array_dim = len(xx_r.shape)
        num_elements = 1
        for j in range(0, array_dim):
          num_elements = num_elements * xx_r.shape[j]
        flattened_array_r = reshape(xx_r,(num_elements,))
        for j in range(0, num_elements): 
          data_r.append(flattened_array_r[j])
        if xx_i != None:
          flattened_array_i = reshape(xx_i,(num_elements,))
          for j in range(0, num_elements): 
            data_i.append(flattened_array_i[j])
        else:
          if not self.errors_plot:
            for j in range(0, num_elements): 
              data_i.append(0.0)

# add data to set of curves
      num_rows = len(data_r)
      if num_rows == 0:
        print 'nothing to update!'
        return
      _dprint(2, 'main key ', self._label_r)
#      if self.errors_plot and self._is_complex == False:
      if self.errors_plot and self._string_tag.find(self.error_tag)>= 0:
        if self._plotter_dict.has_key(self._label_r) == False:
#add the new data to a 'dict' of visualization lists
          self._plotter_dict[self._label_r] = data_r
          _dprint(2, 'assigned error data to self._plotter_dict key ', self._label_r)
          self._plotterlabels_dict[self._label_r] = self._data_labels
          self._plotterlabels_start[self._label_r] = start_pos
        else:
          prev_data_length = len(self._plotter_dict[self._label_r])
          self._plotter_dict[self._label_r] = self._plotter_dict[self._label_r] + data_r
          self._plotterlabels_dict[self._label_r] = self._plotterlabels_dict[self._label_r] + self._data_labels
          for i in range(0,len(start_pos)):
            start_pos[i] = start_pos[i] + prev_data_length
          self._plotterlabels_start[self._label_r] = self._plotterlabels_start[self._label_r] + start_pos
      else:
        if self._plotter_dict.has_key(self._label_r) == False:
#add the new data to a 'dict' of visualization lists
          self._plotter_dict[self._label_r] = data_r
          self._plotterlabels_dict[self._label_r] = self._data_labels
          self._plotterlabels_start[self._label_r] = start_pos
        else:
          prev_data_length = len(self._plotter_dict[self._label_r])
          _dprint(2, 'initial data length ', prev_data_length)
          _dprint(2, 'starting position length ', self._plotterlabels_start[self._label_r])
          self._plotter_dict[self._label_r] = self._plotter_dict[self._label_r] + data_r
          self._plotterlabels_dict[self._label_r] = self._plotterlabels_dict[self._label_r] + self._data_labels
          for i in range(0,len(start_pos)):
            start_pos[i] = start_pos[i] + prev_data_length
          self._plotterlabels_start[self._label_r] = self._plotterlabels_start[self._label_r] + start_pos
        if self._plotter_dict.has_key(self._label_i) == False:
#add the new data to a 'dict' of visualization lists
          self._plotter_dict[self._label_i] = data_i
        else:
          self._plotter_dict[self._label_i] = self._plotter_dict[self._label_i] + data_i

#      print 'self._plotterlabels_dict ', self._plotterlabels_dict 
      # if this is a new item_tag, add a new plot,
      # otherwise, replace old one
      plot_key = self._string_tag + '_plot'
      _dprint(3, 'plot key is ', plot_key)
      if self._xy_plot_dict.has_key(plot_key) == False: 
#        if self._plot_title is None:
#          self._plot_title = self._plot_type +':'
#        self._plot_title = self._plot_title + ' ' + self._tag
#        self._plot_title = self._plot_title + ' ' + string_color
#        self.plot.setTitle(self._plot_title)
        if not self._plot_title is None:
          self.plot.setTitle(self._plot_title)
        if not self._plot_y_axis_label is None:
          self.plot.setAxisTitle(QwtPlot.yLeft, self._plot_y_axis_label)
        if not self._plot_x_axis_label is None:
          self.plot.setAxisTitle(QwtPlot.xBottom, self._plot_x_axis_label)

# if we have x, y data
        if self._is_complex == True or self.errors_plot == False:
          key_plot = self.plot.insertCurve(plot_key)
          self._xy_plot_dict[plot_key] = key_plot
          self._xy_plot_color[plot_key] = self._plot_color
          self.plot.setCurvePen(key_plot, QPen(self._plot_color))
          line_style = self.line_style_table[self.plot_line_style]
          self.plot.setCurveStyle(key_plot, line_style)
          plot_curve = self.plot.curve(key_plot)
          _dprint(3, 'self.plot_symbol ', self.plot_symbol)
          plot_symbol = self.symbol_table[self.plot_symbol]
          _dprint(3, 'self.plot_symbol_size ', self.plot_symbol_size)
          plot_curve.setSymbol(QwtSymbol(plot_symbol, QBrush(self._plot_color),
                     QPen(self._plot_color), QSize(self.plot_symbol_size, self.plot_symbol_size)))

# do we have error data
        if self.errors_plot and self._string_tag.find(self.error_tag)>= 0:
#        if self.errors_plot and self._is_complex == False:
          self._xy_plot_dict[plot_key] = -1
          self.x_errors = QwtErrorPlotCurve(self.plot,self._plot_color,2);
          _dprint(3, 'self.x_errors set to ', self.x_errors)
          self.x_errors.setXErrors(True)
          self.plot.insertCurve(self.x_errors);
          _dprint(3, 'self.x_errors stored in self._x_errors_dict with key ', plot_key)
          self._x_errors_dict[plot_key] = self.x_errors
          self.y_errors = QwtErrorPlotCurve(self.plot,self._plot_color,2);
          _dprint(3, 'self.y_errors set to ', self.y_errors)
          self._y_errors_dict[plot_key] = self.y_errors
          self.plot.insertCurve(self.y_errors);
    # end of x_vs_y_plot 

# data for plot has been gathered together after tree traversal
# now update plot curves, etc
    def update_plot(self):
      plot_keys = self._xy_plot_dict.keys()
      _dprint(3, 'in update_plot xy_plot_dict plot_keys ', plot_keys)
      temp_keys = self._plotter_dict.keys()
      _dprint(3, 'in update_plot plotter_dict keys ', temp_keys)
      error_keys = self._x_errors_dict.keys()
      _dprint(3, 'in update_plot x_errors_dict keys ', error_keys)
      for i in range(0, len(plot_keys)): 
        current_plot_key = plot_keys[i]
        _dprint(3, 'iter current plot key ', i, ' ',current_plot_key)
        data_r = None
        data_i = None
        data_errors = None
        data_key_i = current_plot_key + '_i'
        if self._plotter_dict.has_key(data_key_i):
          data_i = self._plotter_dict[data_key_i]
          if not data_i is None:
            _dprint(3, 'data_i assigned', data_i)
        data_key_r = current_plot_key + '_r'
        if self.errors_plot: 
          if data_key_r.find(self.error_tag) >= 0:
            if self._plotter_dict.has_key(data_key_r):
              data_errors = self._plotter_dict[data_key_r]
              if not data_errors is None:
                _dprint(3, 'data_errors assigned', data_errors)
          else:
            if self._plotter_dict.has_key(data_key_r):
              data_r = self._plotter_dict[data_key_r]
              if not data_r is None:
                _dprint(3, 'data_r assigned', data_r)
        else:
          if self._plotter_dict.has_key(data_key_r):
            data_r = self._plotter_dict[data_key_r]
            if not data_r is None:
              _dprint(3, 'data_r assigned', data_r)
        if not data_errors is None:
          _dprint(3, 'data_errors current plot key ',current_plot_key)
          _dprint(3, 'x_errors_dict keys ', error_keys)
          if self._x_errors_dict.has_key(current_plot_key):
            self.x_errors = self._x_errors_dict[current_plot_key]
            _dprint(3, 'self.x_errors ', self.x_errors)
            self.x_errors.setErrors(data_errors)
            _dprint(3, 'x data errors set in plot')
          if self._y_errors_dict.has_key(current_plot_key):
            self.y_errors = self._y_errors_dict[current_plot_key]
            _dprint(3, 'self.y_errors ', self.y_errors)
            self.y_errors.setErrors(data_errors)
            _dprint(3, 'y data errors set in plot')
        else:
          _dprint(3, 'setting data values')
          key_plot = self._xy_plot_dict[current_plot_key] 
          if data_i is None:
            data_i = []
            for i in range(len(data_r)):
              data_i.append(0.0)           
          self.plot.setCurveData(key_plot, data_r, data_i)
          _dprint(3, 'set data values in plot`')
          if self.errors_plot:
            _dprint(3, 'setting data for errors plot')
# convert data key to error key
            location_value =  current_plot_key.find(self.value_tag)
            error_key = current_plot_key[:location_value] + self.error_tag + '_plot'
            if self._x_errors_dict.has_key(error_key):
              self.x_errors = self._x_errors_dict[error_key]
              self.x_errors.setData(data_r,data_i)
              _dprint(3, 'set data values for x errors')
            if self._y_errors_dict.has_key(error_key):
              self.y_errors = self._y_errors_dict[error_key]
              self.y_errors.setData(data_r,data_i)
              _dprint(3, 'set data values for y errors')


# plot circles in real vs imaginary plot?
        if not self.errors_plot and self.plot_mean_circles:
          sum_r = 0.0
          sum_i = 0.0
          for j in range(0, len(data_r)): 
            sum_r = sum_r + data_r[j]
            sum_i = sum_i + data_i[j]
          avg_r = sum_r / len(data_r)
          avg_i = sum_i / len(data_i)
          x_sq = pow(avg_r, 2)
          y_sq = pow(avg_i, 2)
          radius = sqrt(x_sq + y_sq)
          self._plot_color = self._xy_plot_color[current_plot_key] 
          self.compute_circles (current_plot_key, radius)
          if self.plot_mean_arrows:
            self.compute_arrow (current_plot_key, avg_r, avg_i)
      self.plot.replot()
    # end of update_plot 


    def go(self, counter):
      """Create and plot some garbage data
      """
      item_tag = 'test'
      xx = self._radius * cos(self._angle/57.2957795)
      yy = self._radius * sin(self._angle/57.2957795)

      x_pos = zeros((20,),Float64)
      y_pos = zeros((20,),Float64)
      for j in range(0,20) :
        x_pos[j] = xx + random.random()
        y_pos[j] = yy + random.random()

      # if this is a new item_tag, add a new plot,
      # otherwise, replace old one
      plot_key = item_tag + '_plot'
      self._plot_color = self.color_table["red"]
      if self._xy_plot_dict.has_key(plot_key) == False: 
        key_plot = self.plot.insertCurve(plot_key)
        self._xy_plot_dict[plot_key] = key_plot
        self.plot.setCurvePen(key_plot, QPen(self._plot_color))
        self.plot.setCurveData(key_plot, x_pos, y_pos)
        self.plot.setCurveStyle(key_plot, QwtCurve.Dots)
        self.plot.setTitle("Real vs Imaginary Demo")
        plot_curve = self.plot.curve(key_plot)
        plot_symbol = self.symbol_table["circle"]
        plot_curve.setSymbol(QwtSymbol(plot_symbol, QBrush(self._plot_color),
                     QPen(self._plot_color), QSize(10, 10)))
      else:
        key_plot = self._xy_plot_dict[plot_key] 
        self.plot.setCurveData(key_plot, x_pos, y_pos)

      avg_r = x_pos.mean()
      avg_i = y_pos.mean()
      if self.plot_mean_circles:
        x_sq = pow(avg_r, 2)
        y_sq = pow(avg_i, 2)
        radius = sqrt(x_sq + y_sq)
        self.compute_circles (item_tag, radius)
        self.compute_arrow (item_tag, avg_r, avg_i)
      if counter == 0:
        self.clearZoomStack()
      else:
        self.plot.replot()

    # go()

    def go_errors(self, counter):
      """Create and plot some garbage error data
      """
      item_tag = 'test'
      self._radius = 0.9 * self._radius

      self.gain = 0.95 * self.gain
      num_points = 10
      x_pos = zeros((num_points,),Float64)
      y_pos = zeros((num_points,),Float64)
      x_err = zeros((num_points,),Float64)
      y_err = zeros((num_points,),Float64)
      for j in range(0,num_points) :
        x_pos[j] = self._radius + 3 * random.random()
        y_pos[j] = self._radius + 2 * random.random()
        x_err[j] = self.gain * 3 * random.random()

      # if this is a new item_tag, add a new plot,
      # otherwise, replace old one
      plot_key = item_tag + '_plot'
      self._plot_color = self.color_table["red"]
      if self._xy_plot_dict.has_key(plot_key) == False: 
        key_plot = self.plot.insertCurve(plot_key)
        self._xy_plot_dict[plot_key] = key_plot
        self.plot.setCurvePen(key_plot, QPen(self._plot_color))
        self.plot.setCurveData(key_plot, x_pos, y_pos)
        self.plot.setCurveStyle(key_plot, QwtCurve.Dots)
        self.plot.setTitle("Errors Demo")
        plot_curve = self.plot.curve(key_plot)
        plot_symbol = self.symbol_table["circle"]
#        plot_curve.setSymbol(QwtSymbol(plot_symbol, QBrush(self._plot_color),
#                     QPen(self._plot_color), QSize(10, 10)))
        plot_curve.setSymbol(QwtSymbol(
            QwtSymbol.Cross, QBrush(), QPen(Qt.yellow, 2), QSize(7, 7)))


        self.x_errors = QwtErrorPlotCurve(self.plot,Qt.blue,2);
# add in positions of data to the error curve
        self.x_errors.setData(x_pos,y_pos);
# add in errors to the error curve
        self.x_errors.setXErrors(True)
        self.x_errors.setErrors(x_err);
        self.plot.insertCurve(self.x_errors);
        self.y_errors = QwtErrorPlotCurve(self.plot,Qt.blue,2);
        self.y_errors.setData(x_pos,y_pos);
        self.y_errors.setErrors(x_err);
        self.plot.insertCurve(self.y_errors);
      else:
        key_plot = self._xy_plot_dict[plot_key] 
        self.plot.setCurveData(key_plot, x_pos, y_pos)

        self.x_errors.setData(x_pos,y_pos);
        self.x_errors.setErrors(x_err);
        self.y_errors.setData(x_pos,y_pos);
        self.y_errors.setErrors(x_err);

      if counter == 0:
        self.clearZoomStack()
      else:
        self.plot.replot()
    # go_errors()

    def clearZoomStack(self):
        """Auto scale and clear the zoom stack
        """
        self.plot.replot()
        self.zoomer.setZoomBase()
    # clearZoomStack()

    def start_timer(self, time):
        timer = QTimer(self.plot)
        timer.connect(timer, SIGNAL('timeout()'), self.timerEvent)
        timer.start(time)

    # start_timer()

    def timerEvent(self):
      self._angle = self._angle + 5;
      self._radius = 5.0 + 2.0 * random.random()
      self.index = self.index + 1
      self.go(self.index)
# for testing error plotting
#      self.go_errors(self.index)
    # timerEvent()

    def zoom(self,on):
        self.zoomer.setEnabled(on)
# set fixed scales for realvsimag plot - zooming doesn't work well 
# with autoscaling!!
        if on:
          lb = self.plot.axisScale(QwtPlot.yLeft).lBound()
          hb = self.plot.axisScale(QwtPlot.yLeft).hBound()
          self.plot.setAxisScale(QwtPlot.yLeft, lb, hb)
          lb = self.plot.axisScale(QwtPlot.xBottom).lBound()
          hb = self.plot.axisScale(QwtPlot.xBottom).hBound()
          self.plot.setAxisScale(QwtPlot.xBottom, lb, hb)
          self.picker.setRubberBand(QwtPicker.NoRubberBand)
          self.clearZoomStack()
        else:
          self.zoomer.zoom(0)
          self.picker.setRubberBand(QwtPicker.CrossRubberBand)
          self.plot.setAxisAutoScale(QwtPlot.xBottom)
          self.plot.setAxisAutoScale(QwtPlot.yLeft)
          self.plot.replot()
    # zoom()


    def printPlot(self):
        try:
            printer = QPrinter(QPrinter.HighResolution)
        except AttributeError:
            printer = QPrinter()
        printer.setOrientation(QPrinter.Landscape)
        printer.setColorMode(QPrinter.Color)
        printer.setOutputToFile(True)
        printer.setOutputFileName('plot-%s.ps' % qVersion())
        if printer.setup():
            filter = PrintFilter()
            if (QPrinter.GrayScale == printer.colorMode()):
                filter.setOptions(QwtPlotPrintFilter.PrintAll
                                  & ~QwtPlotPrintFilter.PrintCanvasBackground)
            self.plot.printPlot(printer, filter)
    # printPlot()

    def selected(self, points):
        point = points.point(0)
# this gives the position in pixels!!
        xPos = point[0]
        yPos = point[1]
        _dprint(2,'selected: xPos yPos ', xPos, ' ', yPos);
    # selected()


    
# class realvsimag_plotter


def main(args):
    app = QApplication(args)
    demo = make()
    app.setMainWidget(demo.plot)
    app.exec_loop()

# main()

def make():
    demo = realvsimag_plotter('plot_key')
# for real vs imaginary plot with circles
    demo.set_compute_circles(True)
    demo.start_timer(1000)
    demo.plot.show()
    return demo

# make()

# Admire!
if __name__ == '__main__':
    main(sys.argv)


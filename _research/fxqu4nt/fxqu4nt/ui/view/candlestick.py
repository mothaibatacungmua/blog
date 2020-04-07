from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui, PlotWidget, AxisItem
from typing import List
from datetime import datetime, timedelta

from fxqu4nt.market.bar import OHLC
from fxqu4nt.market.symbol import Symbol


## https://stackoverflow.com/questions/49046931/how-can-i-use-dateaxisitem-of-pyqtgraph
## https://stackoverflow.com/questions/23151612/pyqtgraph-how-to-plot-time-series-date-and-time-on-the-x-axis
## https://stackoverflow.com/questions/42886849/how-to-add-custom-axisitem-to-existing-plotwidget
## https://stackoverflow.com/questions/53629281/how-to-set-the-ticks-in-pyqtgraph
## Create a subclass of GraphicsObject.
## The only required methods are paint() and boundingRect()
## (see QGraphicsItem documentation)
class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  ## data must have fields: time, open, close, min, max
        self.generatePicture()

    def generatePicture(self):
        ## pre-computing a QPicture object allows paint() to run much more quickly,
        ## rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        w = (self.data[1][0] - self.data[0][0]) / 3.
        for (t, open, close, min, max) in self.data:
            p.drawLine(QtCore.QPointF(t, min), QtCore.QPointF(t, max))
            if open > close:
                p.setBrush(pg.mkBrush('r'))
            else:
                p.setBrush(pg.mkBrush('g'))
            p.drawRect(QtCore.QRectF(t - w, open, w * 2, close - open))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        return QtCore.QRectF(self.picture.boundingRect())


class TimeAxisItem(AxisItem):
    def resizeEvent(self, ev=None):
        # s = self.size()

        ## Set the position of the label
        nudge = 5
        br = self.label.boundingRect()
        p = QtCore.QPointF(0, 0)
        if self.orientation == 'left':
            p.setY(int(self.size().height() / 2 + br.width() / 2))
            p.setX(-nudge)
        elif self.orientation == 'right':
            p.setY(int(self.size().height() / 2 + br.width() / 2))
            p.setX(int(self.size().width() - br.height() + nudge))
        elif self.orientation == 'top':
            p.setY(-nudge)
            p.setX(int(self.size().width() / 2. - br.width() / 2.))
        elif self.orientation == 'bottom':
            p.setX(int(self.size().width() / 2. - br.width() / 2.))
            p.setY(int(self.size().height() - br.height() + nudge))
        self.label.setPos(p)
        self.picture = None

MONTH = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

class CandleSticksWidget(PlotWidget):
    def __init__(self, parent: QWidget=None, symbol:Symbol=None, rScrollCallback=None, lScrollCallback=None):
        PlotWidget.__init__(self, parent=parent, axisItems={'bottom': TimeAxisItem('bottom')})
        self.rScrollCallback = rScrollCallback
        self.lScrollCallback = lScrollCallback
        self.symbol = symbol
        self.nDisplayedBars = 100
        self.nTicks = 20
        self.yStep = self.symbol.point * 125

    def resizeEvent(self, ev):
        if self.closed:
            return
        if self.autoPixelRange:
            self.range = QtCore.QRectF(0, 0, self.size().width(), self.size().height())
        PlotWidget.setRange(self, self.range, padding=0, disableAutoPixel=False)  ## we do this because some subclasses like to redefine setRange in an incompatible way.
        self.updateMatrix()

    def _getXRange(self, data: List[OHLC]):
        z = 0
        rebase = [z]
        for i, s in enumerate(data):
            if i > 0:
                diff = (s.Start - data[i-1].Start).total_seconds()
                if diff > 24*2*3600: # exclude two weekend days
                    diff -= 24*2*3600
                z += diff
                rebase.append(z)

        xMin = rebase[0]
        xMax = rebase[-1]
        return xMax, xMin, rebase, data[0].Start

    def _getYRange(self, data: List[OHLC]):
        yMax = -1
        yMin = 10000

        for s in data:
            yMax = max(yMax, s.High)
            yMin = min(yMin, s.Low)
        yMax = yMax - yMax%self.yStep + self.yStep
        yMin = yMin - yMin%self.yStep
        return yMax, yMin

    @staticmethod
    def dtToTickStr(dt: datetime):
        buff = ""
        buff += str(dt.day) + " "
        buff += MONTH[dt.month] + " "
        buff += "%02d"%dt.hour + ":" "%02d"%dt.minute
        return buff

    def draw(self, data: List[OHLC]):
        xMax, xMin, rebaseX, baseX = self._getXRange(data)
        yMax, yMin = self._getYRange(data)
        xStep = (xMax - xMin)/(self.nTicks)

        xTicks = []
        yTicks = []
        for i in range(self.nTicks):
            dt = baseX + timedelta(seconds=xStep*i)
            if dt.weekday() >= 5:
                dt = dt + timedelta(seconds=2*3600*24)
            dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=dt.hour, minute=dt.minute)
            xTicks.append((xStep*i, self.dtToTickStr(dt)))
            yTicks.append((yMin+self.yStep*i, "%0.5f" % (yMin+self.yStep*i)))
        self.setRange(xRange=(xMin, xMax), yRange=(yMin, yMax), disableAutoRange=True)
        bottomAxis = self.plotItem.getAxis("bottom")
        bottomAxis.setTicks([xTicks])

        leftAxis = self.plotItem.getAxis("left")
        leftAxis.setTicks([yTicks])

        print(self.frameGeometry())
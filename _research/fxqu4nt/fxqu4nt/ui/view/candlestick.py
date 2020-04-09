from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg
import bisect
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
    def __init__(self, data, rebase, fsc):
        pg.GraphicsObject.__init__(self)
        self.data: OHLC = data  ## data must have fields: time, open, close, min, max
        self.rebase = rebase
        self.fsc = fsc
        self.generatePicture()

    def generatePicture(self):
        ## pre-computing a QPicture object allows paint() to run much more quickly,
        ## rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        open_ = self.data.Open
        high = self.data.High
        low = self.data.Low
        close_ = self.data.Close
        start = self.data.Start
        end = self.data.End

        diff = (end - start).total_seconds()
        if diff > 24*3600:
            diff -= 24*3600
        if diff > 2*24*3600:
            diff -= 2*24*3600
        start_ = self.rebase
        end_ = self.rebase + diff

        p.drawLine(QtCore.QPointF((start_+end_)/2, low), QtCore.QPointF((start_+end_)/2, high))
        if open_ > close_:
            p.setBrush(pg.mkBrush('r'))
        else:
            p.setBrush(pg.mkBrush('g'))
        p.drawRect(QtCore.QRectF(start_+diff*(self.fsc-1)/(2*self.fsc), open_, diff/self.fsc , close_ - open_))
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
        self.yQ = self.symbol.point * 100
        self.font = QtGui.QFont()
        self.font.setPointSize(9)
        self.padding = 0.03
        self.data = []
        self.rebaseXValues = []
        self.sidx = 0
        self.eidx = 0
        self.pts = 0
        self.fsc = 1.25
        bottomAxis = self.plotItem.getAxis("bottom")
        bottomAxis.setStyle(tickFont=self.font)

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
        dateSet = set()
        for i, s in enumerate(data):
            dt = datetime(year=s.Start.year, month=s.Start.month, day=s.Start.day)
            dateSet.add(dt)
            if i > 0:
                diff = (s.Start - data[i-1].Start).total_seconds()
                if diff >= 24*2*3600: # exclude two weekend days
                    diff -= 24*2*3600
                if diff >= 24*3600: # exclude one weekend days
                    diff -= 24 * 3600
                z += diff
                rebase.append(z)

        return rebase, data[0].Start, dateSet

    def _getYRange(self, data: List[OHLC]):
        yMax = -1
        yMin = 10000

        for s in data[:self.nTicks]:
            yMax = max(yMax, s.High)
            yMin = min(yMin, s.Low)

        yMax = yMax - yMax % self.yQ + self.yQ
        yMin = yMin - yMin % self.yQ
        return yMax, yMin

    @staticmethod
    def dtToTickStr(dt: datetime):
        buff = ""
        buff += str(dt.day) + " "
        buff += MONTH[dt.month] + " "
        buff += "%02d"%dt.hour + ":" "%02d"%dt.minute
        return buff

    def _realRange(self, minV, maxV, padding=None):
        if padding is None:
            return minV, maxV
        p = (maxV - minV) * padding
        return (minV-p), (maxV-p)

    @staticmethod
    def _formDt(dt, dateSet):
        dtOnlyDay = datetime(year=dt.year, month=dt.month, day=dt.day)
        while not dtOnlyDay in dateSet:
            dt = dt + timedelta(seconds=3600 * 24)
            dtOnlyDay = datetime(year=dt.year, month=dt.month, day=dt.day)
        dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=dt.hour, minute=dt.minute)
        return dt

    def getNSampleByLimitPixels(self, computedWidth, padding=100, barPixel=7):
        return int(float(computedWidth - padding)/barPixel - 1)

    def getNTicks(self, computedWidth, padding=80):
        return int(float(computedWidth-padding)/1920 * 30)

    def pixelsToSecond(self, xMin, xMax, computedWidth, padding=80, pixel=2):
        return (xMax - xMin)/(computedWidth-padding) * pixel

    def _computeXAxis(self, data: List[OHLC], computedWidth, padding=100):
        self.nTicks = self.getNTicks(computedWidth, padding)
        rebaseX, baseTime, dateSet = self._getXRange(data)
        rebaseX = [self.fsc*x for x in rebaseX]
        xMin = rebaseX[0]
        xMax = rebaseX[-1]
        timeStep = (xMax - xMin) / (self.nTicks*self.fsc)

        sumStrPixels = 0
        for i in range(self.nTicks):
            dt = self._formDt(baseTime + timedelta(seconds=timeStep*i), dateSet)
            xTickStr = self.dtToTickStr(dt)
            sumStrPixels += QtGui.QFontMetrics(self.font).width(xTickStr)
        avgStrPixesl = sumStrPixels / self.nTicks

        self.nTicks = min(self.nTicks, int((computedWidth - padding) / (avgStrPixesl + 5)))
        midx = bisect.bisect_right(rebaseX, (self.nTicks-1)*timeStep)
        rebaseX = rebaseX[:midx]
        self.rebaseXValues = rebaseX
        xMin = rebaseX[0]
        xMax = rebaseX[-1]
        timeStep = (xMax - xMin) / (self.nTicks * self.fsc)
        return timeStep, rebaseX[:midx], baseTime, dateSet

    def computeXTicks(self, data: List[OHLC], computedWidth):
        timeStep, rebaseX, baseX, dateSet = self._computeXAxis(data, computedWidth)
        xTicks = []
        for i in range(self.nTicks):
            dt = self._formDt(baseX + timedelta(seconds=timeStep*i), dateSet)
            xTicks.append((timeStep*i*self.fsc, self.dtToTickStr(dt)))
        return rebaseX[0], rebaseX[-1], xTicks

    def _computeYAxis(self, data: List[OHLC]):
        yMax, yMin = self._getYRange(data)
        yStep = (yMax - yMin)/self.nTicks
        yStep = yStep - yStep%0.00005
        yMid = (yMin + yMax)/2
        yMid = yMid - yMid%yStep
        yMax = yMid + self.nTicks*yStep*2
        yMin = yMid - self.nTicks*yStep*2

        return yMin, yMax, yStep

    def computeYTicks(self, data: List[OHLC]):
        yMin, yMax, yStep = self._computeYAxis(data)
        yTicks = []
        for i in range(self.nTicks):
            yTicks.append((yMin + yStep *i*4, "%0.5f" % (yMin + yStep * i*4)))
        return yMin, yMax, yTicks

    def draw(self, data: List[OHLC], computedWidth):
        self.data = data[:self.getNSampleByLimitPixels(computedWidth)]
        xMin, xMax, xTicks = self.computeXTicks(self.data, computedWidth)
        yMin, yMax, yTicks = self.computeYTicks(self.data)
        self.data = self.data[:len(self.rebaseXValues)]
        self.setRange(
            xRange=(xMin, xMax),
            yRange=(yMin, yMax),
            disableAutoRange=True,
            padding=self.padding)
        bottomAxis = self.plotItem.getAxis("bottom")
        bottomAxis.setTicks([xTicks])

        leftAxis = self.plotItem.getAxis("left")
        leftAxis.setTicks([yTicks])

        for i in range(len(self.data)):
            item = CandlestickItem(self.data[i], rebase=self.rebaseXValues[i], fsc=self.fsc)
            self.addItem(item)
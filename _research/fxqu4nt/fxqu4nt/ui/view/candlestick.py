from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg
import bisect
from pyqtgraph import QtCore, PlotWidget, AxisItem, Point, QtGui
from pyqtgraph.graphicsItems import ViewBox
from typing import List
from datetime import datetime, timedelta

from fxqu4nt.market.bar import OHLC, BarBase
from fxqu4nt.market.symbol import Symbol


## https://stackoverflow.com/questions/49046931/how-can-i-use-dateaxisitem-of-pyqtgraph
## https://stackoverflow.com/questions/23151612/pyqtgraph-how-to-plot-time-series-date-and-time-on-the-x-axis
## https://stackoverflow.com/questions/42886849/how-to-add-custom-axisitem-to-existing-plotwidget
## https://stackoverflow.com/questions/53629281/how-to-set-the-ticks-in-pyqtgraph
## Create a subclass of GraphicsObject.
## The only required methods are paint() and boundingRect()
## (see QGraphicsItem documentation)
class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data, rebase, fsc, digits=5):
        pg.GraphicsObject.__init__(self)
        self.data: OHLC = data  ## data must have fields: time, open, close, min, max
        self.rebase = rebase
        self.fsc = fsc
        self.generatePicture()
        fmt = "%0." + str(digits) + "f"
        self.setToolTip("Start: " + str(data.Start) + "\n" +
                        "End: " + str(data.End)+"\n" +
                        "Open: " + fmt%data.Open + "\n" +
                        "High: " + fmt%data.High + "\n" +
                        "Low: " + fmt%data.Low + "\n" +
                        "Close: " + fmt%data.Close)

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
        if diff > 2*24*3600:
            diff -= 2*24*3600
        if diff > 24*3600:
            diff -= 24*3600
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
    def __init__(self,
                 parent: QWidget=None,
                 symbol:Symbol=None,
                 barFeed:BarBase=None,
                 startDate=None,
                 endDate=None,
                 initWidth=None):
        PlotWidget.__init__(self, parent=parent, axisItems={'bottom': TimeAxisItem('bottom')})
        self.barFeed = barFeed
        self.startDate = startDate
        self.endDate = endDate
        self.symbol = symbol
        self.nDisplayedBars = 100
        self.nTicks = 20
        self.yQ = self.symbol.point * 100
        self.digits = self.symbol.digits
        self.font = QtGui.QFont()
        self.font.setPointSize(9)
        self.padding = 0.03
        self.data: List[OHLC] = []
        self.displayed: List[OHLC] = []
        self.displayedItems: List[CandlestickItem] = []
        self.sidx = 0
        self.eidx = 0
        self.pts = 0
        self.fsc = 1.25
        self.currentWidth = initWidth
        self.xTicks = []
        self.yTicks = []
        self.resDt = []
        self.rebaseX = []
        self.oldRange = None
        self.bottomAxis = self.plotItem.getAxis("bottom")
        self.leftAxis = self.plotItem.getAxis("left")
        self.displayedMask = []
        self.yRangeUpdating = False
        self.deferNewItems = []
        self.deferNewRebaseX = []
        self.currentYRange = None
        self.initialize()

        self.xTickChanged = False
        self.yTickChanged = False

        self.limit = 10000 # limit 10000 bars in self.data buffer


    def initialize(self):
        self.bottomAxis.setStyle(tickFont=self.font)
        self.leftAxis.setStyle(tickFont=self.font)
        self.data = self.barFeed.fetch(self.startDate, self.endDate)
        self.displayedMask = [False, ] * len(self.data)
        self.displayed = self.data[:self.getNSampleByLimitPixels(self.currentWidth)]

        xMin, xMax, self.xTicks = self.computeXTicks()
        yMin, yMax, self.yTicks = self.computeYTicks()
        self.xTickChanged = True
        self.yTickChanged = True
        self.displayed = self.displayed[:len(self.rebaseX)]
        self.sidx = 0
        self.eidx = len(self.displayed)
        for i in range(self.sidx, self.eidx):
            self.displayedMask[i] = True
        self.currentYRange = (yMin, yMax)
        self.setRange(
            xRange=(xMin, xMax),
            yRange=(yMin, yMax),
            padding=self.padding)
        self.disableAutoRange(0)
        self.disableAutoRange(1)
        self.setMouseEnabled(x=True, y=False)

    def rangeChangedDefault(self, viewBox: ViewBox, newRange):
        # self.emit(QtCore.SIGNAL('viewChanged'), *args)
        self.sigRangeChanged.emit(self, newRange)

    def viewRangeChanged(self, viewBox: ViewBox, newRange):
        if self.yRangeUpdating:
            self.yRangeUpdating = False # avoid loop update y range
            self.oldRange = newRange
            for i, (ci, cv) in enumerate(zip(self.deferNewItems, self.deferNewRebaseX)):
                item = CandlestickItem(ci, rebase=cv, fsc=self.fsc, digits=self.digits)
                self.addItem(item)
            self.deferNewItems = []
            self.deferNewRebaseX = []
            self.rangeChangedDefault(viewBox, newRange)
            return
        newItems = []
        newRebaseX = []
        if self.oldRange == newRange:
            self.rangeChangedDefault(viewBox, newRange)
            return
        if self.oldRange is None:
            self.oldRange = newRange
            newItems = self.displayed
            newRebaseX = self.rebaseX

        diffX = newRange[0][0] - self.oldRange[0][0]
        xTickStep = self.xTicks[1][0] - self.xTicks[0][0]

        if diffX > 0: # scroll from right to left
            # maxRebaseX = self.rebaseX[-1] + diffX
            # print(maxRebaseX, newRange[0][1])
            # minRebaseX = self.rebaseX[0] + diffX
            maxRebaseX = newRange[0][1]
            minRebaseX = newRange[0][0]

            # Get all bar lower than maxRebaseX
            rebase, resDt = self.normalizeDiff(
                self.data[self.eidx-1:], pos="first", posValue=self.rebaseX[-1]/self.fsc)
            rebase = [self.fsc * x for x in rebase]
            rebase = rebase[1:]
            resDt = resDt[1:]
            maxIdx = bisect.bisect_left(rebase, maxRebaseX)
            if maxIdx > 0:
                self.rebaseX = self.rebaseX + rebase[:maxIdx]
                self.resDt = self.resDt + resDt[:maxIdx]
                for i in range(self.eidx, self.eidx+maxIdx):
                    if not self.displayedMask[i]:
                        newItems.append(self.data[i])
                        self.displayedMask[i] = True
                        newRebaseX.append(rebase[i-self.eidx])
                self.eidx += maxIdx

            # Remove all bar lower than minRebaseX
            minIdx = 0
            for i in range(len(self.displayed)):
                if self.rebaseX[i] >= minRebaseX:
                    minIdx = i
                    break
            if minIdx > 0:
                self.rebaseX = self.rebaseX[minIdx:]
                self.resDt = self.resDt[minIdx:]
                self.sidx += minIdx

            # add new tick
            newTickValue = self.xTicks[-1][0] + xTickStep
            if maxRebaseX > newTickValue:
                leftIdx = bisect.bisect_left(self.rebaseX, newTickValue)
                righIdx = leftIdx + 1
                if righIdx < len(self.rebaseX):
                    leftDiff = (newTickValue - self.rebaseX[leftIdx]) / self.fsc
                    rightDiff = (self.rebaseX[righIdx] - newTickValue) / self.fsc
                    if leftDiff > rightDiff:
                        dt = self.resDt[righIdx] - timedelta(seconds=rightDiff)
                    else:
                        dt = self.resDt[leftIdx] + timedelta(seconds=leftDiff)
                    self.xTicks.append((newTickValue, self.dtToTickStr(dt)))
                    self.xTickChanged = True
            # and remove old tick
            # if minRebaseX > self.xTicks[0][0]:
            #     self.xTicks = self.xTicks[1:]
            self.displayed = self.data[self.sidx:self.eidx]
            yMin, yMax, _ = self._computeYAxis(self.displayed)

            if self.currentYRange != (yMin, yMax):
                yMin, yMax, self.yTicks = self.computeYTicks()
                self.yRangeUpdating = True
                self.yTickChanged = True
                self.deferNewItems = newItems
                self.deferNewRebaseX = newRebaseX
                self.currentYRange = (yMin, yMax)
                self.setYRange(min=yMin, max=yMax, padding=self.padding)

        if self.xTickChanged:
            self.bottomAxis.setTicks([self.xTicks])
            self.xTickChanged = False
        if self.yTickChanged:
            self.leftAxis.setTicks([self.yTicks])
            self.yTickChanged = False
        if not self.yRangeUpdating:
            for i, (ci, cv) in enumerate(zip(newItems, newRebaseX)):
                item = CandlestickItem(ci, rebase=cv, fsc=self.fsc, digits=self.digits)
                self.addItem(item)
        self.oldRange = newRange

    def normalizeDiff(self, data: List[OHLC], pos="first", posValue=0.):
        if pos == "first":
            iterD = enumerate(data)
            sidx = 0
            sign = 1
        else:
            iterD = enumerate(reversed(data))
            sidx = -1
            sign = -1
        z = posValue
        rebase = [z]
        resDt = [data[sidx].Start]
        for i, s in iterD:
            if i > 0:
                if s.Start > data[i-1].Start:
                    diff = (s.Start - data[i - 1].Start).total_seconds()
                else:
                    diff = (data[i - 1].Start - s.Start).total_seconds()
                if diff >= 24 * 2 * 3600:  # exclude two weekend days
                    diff -= 24 * 2 * 3600
                if diff >= 24 * 3600:  # exclude one weekend days
                    diff -= 24 * 3600
                z += sign * diff
                resDt.append(s.Start)
                rebase.append(z)
        if sign == 1:
            return rebase, resDt

        return list(reversed(rebase)), list(reversed(resDt))

    def _getXRange(self, data: List[OHLC]):
        return self.normalizeDiff(data, pos="first", posValue=0)

    def _getYRange(self, data: List[OHLC]):
        yMax = -1
        yMin = 10000

        for s in data:
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

    def getNSampleByLimitPixels(self, computedWidth, padding=100, barPixel=7):
        return int(float(computedWidth - padding)/barPixel - 1)

    def getNTicks(self, computedWidth, padding=80):
        return int(float(computedWidth-padding)/1920 * 30)

    def pixelsToSecond(self, xMin, xMax, computedWidth, padding=80, pixel=2):
        return (xMax - xMin)/(computedWidth-padding) * pixel

    def _computeXAxis(self, data: List[OHLC], computedWidth, padding=100):
        self.nTicks = self.getNTicks(computedWidth, padding)
        rebaseX, resDt = self._getXRange(data)
        rebaseX = [self.fsc*x for x in rebaseX]
        xMin = rebaseX[0]
        xMax = rebaseX[-1]
        timeStep = (xMax - xMin) / (self.nTicks*self.fsc)

        sumStrPixels = 0
        for i in range(self.nTicks):
            zt = timeStep*i*self.fsc
            leftIdx = bisect.bisect_left(rebaseX, zt)
            righIdx = leftIdx + 1
            leftDiff = (zt - rebaseX[leftIdx]) / self.fsc
            rightDiff = (rebaseX[righIdx] - zt) / self.fsc
            if leftDiff > rightDiff:
                dt = resDt[righIdx] - timedelta(seconds=rightDiff)
            else:
                dt = resDt[leftIdx] + timedelta(seconds=leftDiff)
            dt = datetime(year=dt.year, month=dt.month, day=dt.day)
            xTickStr = self.dtToTickStr(dt)
            sumStrPixels += QtGui.QFontMetrics(self.font).width(xTickStr)
        avgStrPixesl = sumStrPixels / self.nTicks

        self.nTicks = min(self.nTicks, int((computedWidth - padding) / (avgStrPixesl + 5)))
        midx = bisect.bisect_left(rebaseX, self.nTicks*timeStep*self.fsc)
        rebaseX = rebaseX[:midx]
        self.rebaseX = rebaseX
        xMin = rebaseX[0]
        xMax = rebaseX[-1]
        timeStep = (xMax - xMin) / (self.nTicks * self.fsc)
        return timeStep, rebaseX, resDt[:midx]

    def computeXTicks(self):
        timeStep, rebaseX, resDt = self._computeXAxis(self.displayed, self.currentWidth)
        xTicks = []
        for i in range(self.nTicks):
            zt = timeStep*i*self.fsc
            leftIdx = bisect.bisect_left(rebaseX, zt)
            righIdx = leftIdx + 1
            leftDiff = (zt - rebaseX[leftIdx]) / self.fsc
            rightDiff = (rebaseX[righIdx] - zt) / self.fsc
            if leftDiff > rightDiff:
                dt = resDt[righIdx] - timedelta(seconds=rightDiff)
            else:
                dt = resDt[leftIdx] + timedelta(seconds=leftDiff)
            xTicks.append((timeStep*i*self.fsc, self.dtToTickStr(dt)))
        self.resDt = resDt
        return rebaseX[0], rebaseX[-1], xTicks

    def _computeYAxis(self, data: List[OHLC]):
        yMax, yMin = self._getYRange(data)
        yStep = (yMax - yMin)/self.nTicks
        yStep = yStep - yStep%0.00005
        yMid = (yMin + yMax)/2
        yMid = yMid - yMid%yStep
        yMax = yMid + self.nTicks*yStep
        yMin = yMid - self.nTicks*yStep

        return yMin, yMax, yStep

    def computeYTicks(self):
        yMin, yMax, yStep = self._computeYAxis(self.displayed)
        yTicks = []
        fmt = "%0."+str(self.digits) + "f"

        for i in range(self.nTicks):
            yTicks.append((yMin + yStep*i*2, fmt % (yMin + yStep*i*2)))

        return yMin, yMax, yTicks

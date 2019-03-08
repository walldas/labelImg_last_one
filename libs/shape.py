#!/usr/bin/python
# -*- coding: utf-8 -*-
import math
from scipy.spatial import ConvexHull

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.lib import distance

DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 128)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)


class Shape(object):
    P_SQUARE, P_ROUND = range(2)

    MOVE_VERTEX, NEAR_VERTEX = range(2)

    # The following class variables influence the drawing
    # of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 6
    scale = 1.0

    def __init__(self, label=None, line_color=None,difficult = False):
        self.label = label
        self.points = []
        self.fill = False
        self.selected = False
        self.difficult = difficult
        self.tetragon = False
        self.centerPoint = None
        self.rotationPoint = None
        self.deg = 0
        self.shape3D = False

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color


    def close(self):
        self._closed = True

    def reachMaxPoints(self):
        if len(self.points) >= 4:
            return True
        return False

    def addPoint(self, point):
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False

    def tetragonRotationPoint(self):
        pixelsGoUp=50
        cpp=self.centerPointPosition()
        psiaudoPoints=[self.rotatePoint(cpp,point,-self.deg) for point in self.points]
        minY=min([point.y() for point in psiaudoPoints])- pixelsGoUp
        zeroAnglePoint=QPointF(cpp.x(),minY)
        return self.rotatePoint(cpp,zeroAnglePoint,self.deg)


    def rotatePoint(self,center, point, angle):
        cx,cy=center.x(),center.y()
        x,y=point.x(),point.y()
        radians = (math.pi / 180) * angle
        cos = math.cos(radians)
        sin = math.sin(radians)
        nx = (cos * (x - cx)) + (sin * (y - cy)) + cx
        ny = (cos * (y - cy)) - (sin * (x - cx)) + cy
        return QPointF(nx, ny)

    def lengthBetween2Points(self,pointA,pointB):
        return distance(pointA-pointB)

    def average(self,arr):
        return float(sum(arr)) / max(len(arr), 1)

    def centerPointPosition(self):
        centerPointX=self.average([x.x() for x in self.points])
        centerPointY=self.average([y.y() for y in self.points])
        return QPointF(round(centerPointX),round(centerPointY))

    def paint(self, painter):

        if self.points:
            color = self.select_line_color if self.selected else self.line_color
            pen = QPen(color)
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            painter.setPen(pen)

            line_path = QPainterPath()
            vrtx_path = QPainterPath()

            rotate_path = QPainterPath()
            rotate_path.moveTo(self.points[0])

            center_path = QPainterPath()
            center_path.moveTo(self.points[0])
            try :
                d = self.point_size / self.scale
                self.centerPoint=self.centerPointPosition()
                point=self.tetragonRotationPoint()
                self.rotationPoint=point
                visualFix=QPointF(-self.point_size/2-1,-self.point_size/2-1)
                if self.selected:
                    if self.tetragon:
                        point=self.tetragonRotationPoint()
                        self.rotationPoint=point
                    #paint rotation dot
                    point=point+visualFix
                    rotate_path.addRect(point.x(), point.y(), d, d)
                    painter.drawPath(rotate_path)
                    #fill dot
                    painter.fillPath(rotate_path, self.vertex_fill_color)
                    #paint center point
                    point=self.centerPoint+visualFix
                    center_path.addRect(point.x(), point.y(), d, d)
                    painter.drawPath(center_path)
                else:
                    point = self.points[0]
            except:
                point = self.points[0]

            line_path.moveTo(self.points[0])
            # Uncommenting the following line will draw 2 paths
            # for the 1st vertex, and make it non-filled, which
            # may be desirable.
            # self.drawVertex(vrtx_path, 0)
            for i, p in enumerate(self.points):
                line_path.lineTo(p)
                self.drawVertex(vrtx_path, i)
            if len(self.points)==4:
                line_path.lineTo(self.points[0])
            if len(self.points)==8:
                line_path.lineTo(self.points[0])
                line_path.lineTo(self.points[3])
                line_path.lineTo(self.points[4])
                line_path.lineTo(self.points[7])
                line_path.lineTo(self.points[6])
                line_path.lineTo(self.points[1])
                line_path.lineTo(self.points[2])
                line_path.lineTo(self.points[5])
            if self.isClosed() and self.shape3D==False:
                line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self.vertex_fill_color)
            if self.fill:
                # Color of shape
                color = self.select_fill_color if self.selected else self.fill_color
                if self.shape3D==False:
                    painter.fillPath(line_path, color)
                else:
                    perimeter = self.makePerimeter()
                    painter.fillPath(perimeter, color)

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]

        if i == self._highlightIndex:
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size
        if self._highlightIndex is not None:
            self.vertex_fill_color = self.hvertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
            # print(point)
        else:
            assert False, "unsupported vertex shape"

    def nearestVertex(self, point, epsilon):
        for i, p in enumerate(self.points):

            if distance(p - point) <= epsilon:
                return i
        return None
    def overRotationPoint(self,point,epsilon):
        if distance(self.rotationPoint - point) <= epsilon:
            return True
        return False

    def containsPoint(self, point):
        return self.makePerimeter().contains(point)

    def boundingRect(self):
        return self.makePerimeter().boundingRect()

    def makePerimeter(self):# makes perimeter points
        points=[[point.x(), point.y()] for point in self.points]
        hull = ConvexHull(points)
        perimeterIndex=hull._vertices
        path = QPainterPath(self.points[perimeterIndex[0]])
        for p in perimeterIndex[1:]:
            path.lineTo(self.points[p])
        return path


    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset


    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

    def copy(self):
        shape = Shape("%s" % self.label)
        shape.points = [p for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape.fill_color:
            shape.fill_color = self.fill_color
        shape.difficult = self.difficult

        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value

#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
from libs.canvas import Canvas
from libs.shape import Shape
# from libs.lib import distance
try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

XML_EXT = '.xml'
ENCODE_METHOD = 'utf-8'

class PascalVocWriter:

    def __init__(self, foldername, filename, imgSize,databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.boxlist = []
        self.localImgPath = localImgPath
        self.verified = False

    def prettify(self, elem):
        """
            Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf8')
        root = etree.fromstring(rough_string)
        return etree.tostring(root, pretty_print=True, encoding=ENCODE_METHOD).replace("  ".encode(), "\t".encode())
        # minidom does not support UTF-8
        '''reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t", encoding=ENCODE_METHOD)'''

    def genXML(self):
        """
            Return XML root
        """
        # Check conditions
        if self.filename is None or \
                self.foldername is None or \
                self.imgSize is None:
            return None

        top = Element('annotation')
        if self.verified:
            top.set('verified', 'yes')

        folder = SubElement(top, 'folder')
        folder.text = self.foldername

        filename = SubElement(top, 'filename')
        filename.text = self.filename

        if self.localImgPath is not None:
            localImgPath = SubElement(top, 'path')
            localImgPath.text = self.localImgPath

        source = SubElement(top, 'source')
        database = SubElement(source, 'database')
        database.text = self.databaseSrc

        size_part = SubElement(top, 'size')
        width = SubElement(size_part, 'width')
        height = SubElement(size_part, 'height')
        depth = SubElement(size_part, 'depth')
        width.text = str(self.imgSize[1])
        height.text = str(self.imgSize[0])
        if len(self.imgSize) == 3:
            depth.text = str(self.imgSize[2])
        else:
            depth.text = '1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'
        return top

    def rotateBackPoints(self, xmin, ymin, xmax, ymax, angle):
        center=QPointF((xmin+xmax)/2,(ymin+ymax)/2)

        k0=Shape.rotatePoint(self,center,QPointF(xmin,ymin),-angle)
        k2=Shape.rotatePoint(self,center,QPointF(xmax,ymax),-angle)
        rotatedPoints=[k0,k2]
        points= [(int(point.x()),int(point.y())) for point in rotatedPoints]
        return points

    def addBndBox(self, xmin, ymin, xmax, ymax, name, difficult, tetragon, angle):
        if angle==0 or angle==360:
            bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        else:
            bndbox={}
            rotatedPoints=self.rotateBackPoints(xmin, ymin, xmax, ymax, angle)
            bndbox['xmin']=rotatedPoints[0][0]
            bndbox['ymin']=rotatedPoints[0][1]
            bndbox['xmax']=rotatedPoints[1][0]
            bndbox['ymax']=rotatedPoints[1][1]
        bndbox['name'] = name
        bndbox['difficult'] = difficult
        bndbox['tetragon'] = tetragon
        bndbox['angle'] = angle
        bndbox['shape3D'] = False
        self.boxlist.append(bndbox)

    def addBndBox2(self, points, name, difficult, tetragon, angle):
        bndbox={}
        bndbox['shape3D'] = False
        bndbox['name'] = name
        bndbox['difficult'] = difficult
        bndbox['tetragon'] = tetragon
        bndbox['angle'] = angle
        bndbox['k0x']=points[0][0]
        bndbox['k0y']=points[0][1]
        bndbox['k1x']=points[1][0]
        bndbox['k1y']=points[1][1]
        bndbox['k2x']=points[2][0]
        bndbox['k2y']=points[2][1]
        bndbox['k3x']=points[3][0]
        bndbox['k3y']=points[3][1]
        self.boxlist.append(bndbox)

    def addBndBox3(self, shape3D, points, label, angle, difficult):
        bndbox={}
        bndbox['name'] = label
        bndbox['difficult'] = difficult
        bndbox['angle'] = angle
        bndbox['shape3D'] = shape3D
        bndbox['tetragon'] = False
        i=0
        for point in points:
            k="k"+format(i)
            bndbox[k+'x'] = int(point[0])
            bndbox[k+'y'] = int(point[1])
            i+=1
        self.boxlist.append(bndbox)


    def appendObjects(self, top):
        for each_object in self.boxlist:
            object_item = SubElement(top, 'object')
            name = SubElement(object_item, 'name')
            try:
                name.text = unicode(each_object['name'])
            except NameError:
                # Py3: NameError: name 'unicode' is not defined
                name.text = each_object['name']
            pose = SubElement(object_item, 'pose')
            pose.text = "Unspecified"
            truncated = SubElement(object_item, 'truncated')
            if each_object["shape3D"]==False and each_object["tetragon"]==False:
                if int(each_object['ymax']) == int(self.imgSize[0]) or (int(each_object['ymin'])== 1):
                    truncated.text = "1" # max == height or min
                elif (int(each_object['xmax'])==int(self.imgSize[1])) or (int(each_object['xmin'])== 1):
                    truncated.text = "1" # max == width or min
                else:
                    truncated.text = "0"
            else:
                truncated.text = "0"
            difficult = SubElement(object_item, 'difficult')
            difficult.text = str( bool(each_object['difficult']) & 1 )

            tetragon= SubElement(object_item, 'tetragon')
            tetragon.text=str(each_object['tetragon'])

            shape3D= SubElement(object_item, 'shape3D')
            shape3D.text=str(each_object['shape3D'])

            angle= SubElement(object_item, 'angle')
            angle.text=str(each_object['angle'])
            bndbox = SubElement(object_item, 'bndbox')
            if each_object["shape3D"]==False:
                if each_object['tetragon']==False:
                    xmin = SubElement(bndbox, 'xmin')
                    xmin.text = str(each_object['xmin'])
                    ymin = SubElement(bndbox, 'ymin')
                    ymin.text = str(each_object['ymin'])
                    xmax = SubElement(bndbox, 'xmax')
                    xmax.text = str(each_object['xmax'])
                    ymax = SubElement(bndbox, 'ymax')
                    ymax.text = str(each_object['ymax'])
                elif each_object['tetragon']==True:
                    k0x = SubElement(bndbox, 'k0x')
                    k0x.text = str(int(round(each_object['k0x'],0)))
                    k0y = SubElement(bndbox, 'k0y')
                    k0y.text = str(int(round(each_object['k0y'],0)))
                    k1x = SubElement(bndbox, 'k1x')
                    k1x.text = str(int(round(each_object['k1x'],0)))
                    k1y = SubElement(bndbox, 'k1y')
                    k1y.text = str(int(round(each_object['k1y'],0)))
                    k2x = SubElement(bndbox, 'k2x')
                    k2x.text = str(int(round(each_object['k2x'],0)))
                    k2y = SubElement(bndbox, 'k2y')
                    k2y.text = str(int(round(each_object['k2y'],0)))
                    k3x = SubElement(bndbox, 'k3x')
                    k3x.text = str(int(round(each_object['k3x'],0)))
                    k3y = SubElement(bndbox, 'k3y')
                    k3y.text = str(int(round(each_object['k3y'],0)))
            elif each_object["shape3D"]:
                k0x = SubElement(bndbox, 'k0x')
                k0x.text = str(each_object['k0x'])
                k0y = SubElement(bndbox, 'k0y')
                k0y.text = str(each_object['k0y'])
                k1x = SubElement(bndbox, 'k1x')
                k1x.text = str(each_object['k1x'])
                k1y = SubElement(bndbox, 'k1y')
                k1y.text = str(each_object['k1y'])
                k2x = SubElement(bndbox, 'k2x')
                k2x.text = str(each_object['k2x'])
                k2y = SubElement(bndbox, 'k2y')
                k2y.text = str(each_object['k2y'])
                k3x = SubElement(bndbox, 'k3x')
                k3x.text = str(each_object['k3x'])
                k3y = SubElement(bndbox, 'k3y')
                k3y.text = str(each_object['k3y'])
                k4x = SubElement(bndbox, 'k4x')
                k4x.text = str(each_object['k4x'])
                k4y = SubElement(bndbox, 'k4y')
                k4y.text = str(each_object['k4y'])
                k5x = SubElement(bndbox, 'k5x')
                k5x.text = str(each_object['k5x'])
                k5y = SubElement(bndbox, 'k5y')
                k5y.text = str(each_object['k5y'])
                k6x = SubElement(bndbox, 'k6x')
                k6x.text = str(each_object['k6x'])
                k6y = SubElement(bndbox, 'k6y')
                k6y.text = str(each_object['k6y'])
                k7x = SubElement(bndbox, 'k7x')
                k7x.text = str(each_object['k7x'])
                k7y = SubElement(bndbox, 'k7y')
                k7y.text = str(each_object['k7y'])


    def save(self, targetFile=None):
        root = self.genXML()
        self.appendObjects(root)
        out_file = None
        if targetFile is None:
            out_file = codecs.open(self.filename + XML_EXT, 'w', encoding=ENCODE_METHOD)
        else:
            out_file = codecs.open(targetFile, 'w', encoding=ENCODE_METHOD)
        prettifyResult = self.prettify(root)
        out_file.write(prettifyResult.decode('utf8'))
        out_file.close()



class PascalVocReader:

    def __init__(self, filepath):
        self.shapes = []
        self.filepath = filepath
        self.verified = False
        self.imagePath = ""
        self.parseXML()

    def getShapes(self):
        return self.shapes

    def makeBackRotatedShape(self, points, angle):
        canvas=Canvas()
        shape=Shape()
        xmax=points[2][0]
        xmin=points[0][0]
        ymax=points[2][1]
        ymin=points[0][1]

        shape.centerPoint=QPointF(( xmin+xmax)/2,(ymin+ymax)/2)
        shape.points= [QPointF(point[0],point[1]) for point in points]
        rotatedShapePoints=canvas.getRotatedShape(shape,angle)
        points= [(round(point.x(),0),round(point.y(),0)) for point in rotatedShapePoints]

        return points

    def addShape(self, label, bndbox, difficult, angle):
        if angle==360:
            angle=0
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)
        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        tetragon=False
        if angle>0:
            points=self.makeBackRotatedShape(points, angle)
            # print(points)
        self.shapes.append((label, points, None, None, difficult, tetragon, angle,False))

    def addShape2(self,label, bndbox, difficult, angle):
        k0x = int(bndbox.find('k0x').text)
        k0y = int(bndbox.find('k0y').text)
        k1x = int(bndbox.find('k1x').text)
        k1y = int(bndbox.find('k1y').text)
        k2x = int(bndbox.find('k2x').text)
        k2y = int(bndbox.find('k2y').text)
        k3x = int(bndbox.find('k3x').text)
        k3y = int(bndbox.find('k3y').text)
        points=[(k0x,k0y),(k1x,k1y),(k2x,k2y),(k3x,k3y)]
        tetragon=True
        self.shapes.append((label, points, None, None, difficult, tetragon, angle,False))
        # print(self.shapes)

    def addShape3(self, label, bndbox, difficult, angle):
        # print("kolkas veikia iki tiek")
        points=[]
        numberOfPoints,i=8,0
        shape3D=True
        while numberOfPoints>i:
            k="k"+format(i)
            x=int(bndbox.find(k +'x').text)
            y=int(bndbox.find(k +'y').text)
            points.append((x,y))
            i+=1
        self.shapes.append((label, points, None, None, difficult,False, angle, shape3D))

    def parseXML(self):
        assert self.filepath.endswith(XML_EXT), "Unsupport file format"
        parser = etree.XMLParser(encoding=ENCODE_METHOD)
        xmltree = ElementTree.parse(self.filepath, parser=parser).getroot()
        filename = xmltree.find('filename').text
        self.imagePath = xmltree.find('path').text
        try:
            verified = xmltree.attrib['verified']
            if verified == 'yes':
                self.verified = True
        except KeyError:
            self.verified = False

        for object_iter in xmltree.findall('object'):
            bndbox = object_iter.find("bndbox")
            label = object_iter.find('name').text
            try:
                tetragon=self.trueFalse(object_iter.find('tetragon').text)
            except:
                tetragon=False
            difficult = False
            try:
                angle=int(object_iter.find('angle').text)
            except:
                angle=0
            try:
                shape3D=self.trueFalse(object_iter.find('shape3D').text)
            except:
                shape3D=False
            if object_iter.find('difficult') is not None:
                difficult = bool(int(object_iter.find('difficult').text))
            if tetragon and shape3D==False:
                # print("keturkampis")
                self.addShape2(label, bndbox, difficult, angle)
            elif shape3D:
                # print("3d figura")
                self.addShape3(label, bndbox, difficult, angle)
            elif tetragon==False and shape3D==False:
                # print("paprasta figura")
                self.addShape(label, bndbox, difficult, angle)
            else:
                print("bad shape upload")
        return True

    def trueFalse(self,stri):
        if stri=="True" or stri==True:
            return (True)
        else:
            return (False)

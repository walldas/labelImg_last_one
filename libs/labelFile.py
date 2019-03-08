# Copyright (c) 2016 Tzutalin
# Create by TzuTaLin <tzu.ta.lin@gmail.com>

try:
    from PyQt5.QtGui import QImage
except ImportError:
    from PyQt4.QtGui import QImage

from base64 import b64encode, b64decode
from libs.pascal_voc_io import PascalVocReader
from libs.pascal_voc_io import PascalVocWriter
from libs.pascal_voc_io import XML_EXT
import os.path
import sys


def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except:
        return default



class LabelFileError(Exception):
    pass


class LabelFile(object):
    # It might be changed as window creates
    suffix = '.xml'

    def __init__(self, filename=None):
        if filename is not None:
            reader = PascalVocReader(filename)
            self.shapes = reader.getShapes()
            self.imagePath = reader.imagePath
            self.imageData = read(self.imagePath, None)
            self.verified = reader.verified
        else:
            self.shapes = ()
            self.imagePath = None
            self.imageData = None
            self.verified = False


    def savePascalVocFormat(self, filename, shapes, imagePath, imageData,
                            lineColor=None, fillColor=None, databaseSrc=None):
        imgFolderPath = os.path.dirname(imagePath)
        imgFolderName = os.path.split(imgFolderPath)[-1]
        imgFileName = os.path.basename(imagePath)
        #imgFileNameWithoutExt = os.path.splitext(imgFileName)[0]
        # Read from file path because self.imageData might be empty if saving to
        # Pascal format
        image = QImage()
        image.load(imagePath)
        imageShape = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]
        writer = PascalVocWriter(imgFolderName, imgFileName,
                                 imageShape, localImgPath=imagePath)
        writer.verified = self.verified

        for shape in shapes:
            points = shape['points']
            label = shape['label']
            difficult = int(shape['difficult'])
            tetragon=shape['tetragon']
            angle=int(round(shape['deg']))
            d3=shape['shape3D']
            if d3==False:
                if tetragon==False:
                    bndbox = LabelFile.convertPoints2BndBox(points)
                    writer.addBndBox(bndbox[0], bndbox[1], bndbox[2], bndbox[3], label, difficult, tetragon, angle)
                elif tetragon==True:
                    writer.addBndBox2(points,label,difficult,tetragon,angle)
            elif d3:
                writer.addBndBox3(d3,points,label, angle, difficult)


        writer.save(targetFile=filename)
        return

    def saveDarknetTxtFormat(self, imagePath, image, shapes, labelList):
        imgFileNameWithoutExt = os.path.splitext(imagePath)[0]
        annotationFilePath = imgFileNameWithoutExt + ".txt"
        shapeText = ""
        for shape in shapes:
            angle=shape['deg']/360
            shapeText += str(labelList.index(shape["label"])) + " "
            if shape['tetragon']==False:
                bbox = LabelFile.convertPoint2BBox(shape["points"], image.width(), image.height())
                shapeText += str(bbox[0] + (bbox[2] / 2)) + " " +\
                            str(bbox[1] + (bbox[3] / 2)) + " " + \
                            str(bbox[2] - bbox[0]) +" " +\
                            str(bbox[3] - bbox[1]) +" "+\
                            str(angle) + "\n"
            elif shape['tetragon']==True:
                abox = LabelFile.convertPoints2ZeroOneScale(shape["points"], image.width(), image.height())
                for item in abox:
                    shapeText += str(item)+" "
                shapeText += str(angle) + "\n"
        # print("Darknet annotation goes to: " + annotationFilePath)
        f = open(annotationFilePath, 'w')
        f.write(shapeText)
        f.close()
        return

    def toggleVerify(self):
        self.verified = not self.verified

    @staticmethod
    def convertPoints2ZeroOneScale(points, width, height):
        scaledPoints=[(round(point[0])/width,round(point[1])/height) for point in points]
        scaledPointsInOneList=[subPoint for point in scaledPoints for subPoint in point ]
        return scaledPointsInOneList

    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix

    @staticmethod
    def convertPoints2BndBox(points):
        xmin=points[0][0]
        ymin=points[0][1]
        xmax=points[2][0]
        ymax=points[2][1]
        if xmin < 1:
            xmin = 1
        if ymin < 1:
            ymin = 1
        return int(xmin), int(ymin), int(xmax), int(ymax)

    @staticmethod
    def convertPoint2BBox(points, width, height):
        dw = 1.0 / float(width)
        dh = 1.0 / float(height)
        bndBox = LabelFile.convertPoints2BndBox(points)
        return float(bndBox[0]) * dw, float(bndBox[1]) * dh, float(bndBox[2]) * dw, float(bndBox[3]) * dh

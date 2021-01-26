#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#                                       Created by AR for Amorphyx, Inc
#                             Last edit on 24 Jan 2021 - Validated on 25 Jan 2021
#
#                          THIS CODE REQUIRES ALL MODULES IN THIS REPOSITORY TO RUN
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
import re                                                                       #Regex, used for sorting and parsing
import math                                                                     #Used for math functions like trig
import itertools                                                                #Used for iterating in the parsers
import operator                                                                 #Used for parsing
import Part, PartGui                                                            #Required for using FreeCAD parts
from FreeCAD import Base                                                        #Required for some functions in freecad
import xml.etree.ElementTree as ET                                              #Required to read the lyp (layer properties) file
import DraftGeomUtils                                                           #Used for FreeCAD operations
import numpy as np                                                              #Used for arrays and array functions
import heapq                                                                    #Used for sorting
import random                                                                   #Used for color generation
from PySide import QtGui, QtCore                                                #Used for GUI interface for import/export files
'''
Below imports are the imports for the external functions. All of them get passed and return information, but none of them make permanent changes
or updates, all updates to major variables come from the main script here.
'''
class WorkingEnvironment(QtGui.QDialog):
    def __init__(self):
        super(WorkingEnvironment, self).__init__()
        self.initUI()
    def initUI(self):
        reply = QtGui.QMessageBox.information(None,"","Select the folder containing the supporting python modules.")
        accept = QtGui.QPushButton("Select Folder")
        accept.clicked.connect(self.acceptClicked)
        #
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        buttonBox.addButton(accept, QtGui.QDialogButtonBox.ActionRole)
        #
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        # define window xLoc,yLoc,xDim,yDim
        self.setGeometry(250, 250, 450, 50)
        self.setWindowTitle("Please select working environment.")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    def acceptClicked(self):
        directoryName = QtGui.QFileDialog.getExistingDirectory(parent=self, caption='Select Directory', dir='.')
        if directoryName:
            self.currentEnvironment = directoryName
            self.close()
        else:
            reply = QtGui.QMessageBox.information(None,"","Please select the working environment folder.")
            self.acceptClicked()

import sys, importlib, os                                                       #Used for importing and reloading modules
work = WorkingEnvironment()
work.exec_()
dir_path = work.currentEnvironment #os.path.dirname(os.path.realpath(__file__)) #Sets environment for import modules
#print(dir_path)
sys.path.append(dir_path)                                                       #Adds the path of our modules to the standard system module path
import input_files_Pv1 as files                                                 #Contains all functions for reading the 3 input files
import supporting_functions_Pv1 as sp                                           #Contains various supporting functions called from multiple modules
import bulk_Pv1 as bulk                                                         #Holds the bulk function which creates a substrate
import planarize_Pv1 as planar                                                  #Creates a planarized layer on the top
'''If an error occurs after an update to an imported module then the module likely holds the error, even though FreeCAD does not say that'''
try:                                                                            #Only runs reload if it is needed (not needed on first run through)
    importlib.reload(sys.modules['input_files_Pv1'])                            #Reloads any changes in modules
except:
    print("Reload not needed for input_files_Pv1")
try:                                                                            #Only runs reload if it is needed (not needed on first run through)
    importlib.reload(sys.modules['supporting_functions_Pv1'])                   #Reloads any changes in modules
except:
    print("Reload not needed for supporting_functions_Pv1")
try:                                                                            #Only runs reload if it is needed (not needed on first run through)
    importlib.reload(sys.modules['bulk_Pv1'])                                   #Reloads any changes in modules
except:
    print("Reload not needed for bulk_Pv1")
try:                                                                            #Only runs reload if it is needed (not needed on first run through)
    importlib.reload(sys.modules['planarize_Pv1'])                              #Reloads any changes in modules
except:
    print("Reload not needed for planarize_Pv1")

'''
__author__ = ""
__copyright__ = ""
__credits__ = []
__license__ = "LGPLv3+"
__version__ = VERSION
__maintainer__ = ""
__email__ = ""
__status__ = "Development"
'''

'''
Global array declaration below. These arrays are used in various functions in this main script, but they cannot be properly accessed from the other scripts.
They are global so that they can be appeneded (mutable operator) to each time a function is called (every new layer).
'''
#All below arrays will update inside LayerDevelop function by using the .append (mutable operator)
extrusionLIL1 = []                                                              #Used to house extrusion index names -LIL=ListIndexingLayer
featureLIL1 = []                                                                #Used to house all feature index names (internal names, not labels)
chamfLIL1 = []                                                                  #Used to house all chamfer index names (internal names, not labels)
layerLIL = []                                                                   #Used to house all the layers (FreeCAD references)
holeLIL = []                                                                    #Used to house all the hole layer objects (FreeCAD references)
featureNames =[]                                                                #Used to house all feature names (labels in doc) from layers
chamfNames = []                                                                 #Used to house all chamfer names (labels in doc) from layerDevelop
layerNames = []                                                                 #Used to house all the layer names (FreeCAD names, not XS names)
holeNames = []                                                                  #Used to house all the hole layer names (FreeCAD names)
z_value = [0]                                                                   #Will be used to keep track of current z locations, will be updated for each new layer
layerThickness = []                                                             #Used to keep track of each layer thickness to use in Deposit function
#All below arrays will update inside deposit function by using the .append (mutable operator)
depositLIL = []                                                                 #Used to house all deposit index names (internal names, not labels)
depositNames =[]                                                                #Used to house all feature names (labels in doc) from layers
depositionThickness = []                                                        #Used to keep track of thickness of each deposition for the "stamp" in taper
lastDeposited = []                                                              #Used to keep track of the last layer added (features or deposition)

'''
Code requires objects to be in microns, with output in FreeCAD's standard (mm).
Code does not currently work with curved objects and cannot chamfer objects appearing curved (from straight lines). The latter will still cause issues and the object may not appear.
Code may not work for holes created through multiple more than 2 layers. ***Might have fixed
All layers may be .6um thicker or thinner than designated, due to som FreeCAD limitations with tapering. This also means some features may be up to .6um off as well.
Bias does not work for complex objects or for curved/appearing curved objects
Currently max layer height is designed for 50 mm, any larger and the deposit function will not work - this can be edited inside the extrude in deposit()
Expected input units of gds2 file is in microns; other units are accepted, but all points are divided by 1000 to try to convert to FreeCAD native units of mm
'''


def layerDevelop(all_polygons_dict, layerNum, layer_thickness, angle, bias = 0):#Creates each layer (not interacting with holes) based off of the given features
    '''
    The layerDevelop function is the primary feature creation function. It creates all features that do not interact with holes and calls the taper function.

    Function updates extrusionLIL1, featureLIL1, featureNames, layerNames, layerLIL, layerThickness, z_value, and lastDeposited arrays

    Inputs: the polygon dictionary, the layer number (from XS script), the layer thickness, the taper/chamfer angle (0 if no taper), and a bias value if applicable.

    Returns nothing currently, but can return the final layer object (fused from all the features).
    '''

    print("layerDevelop Start")                                                 #For debugging
    numOfExt = len(extrusionLIL1)                                               #Total number of extrusions, for offsetting
    numOfFeat = len(featureLIL1)                                                #Total number of features, for offsetting
    numOfChamf = len(chamfLIL1)                                                 #Total number of extrusions, for offsetting
    numOfFeatNames = len(featureNames)                                          #Total number of feature names, for offsetting
    numOfChamfNames = len(chamfNames)                                           #Total number of chamfer names, for offsetting
    layerThickness.append(layer_thickness)
    if len(layerNames) != 0:
        highestPoint, highestObj = sp.get_highest_point(True,False)                 #Retrieves the highest Z value and the layer associated with it
    else:
        highestObj = FreeCAD.ActiveDocument.getObject("Substrate")

    if len(FreeCAD.ActiveDocument.Objects) == 1:                                #If only have the substrate, so this is first deposit layer
        for f in range(0,len(all_polygons_dict[layerNum])):                     #Goes through all polygons in given key (layerNum)
            polyLayer = sp.get_xy_points(all_polygons_dict[layerNum][f])        #Converts all to mm
            for point in polyLayer:
                point.append(z_value[-1])
            print("Before layerDevelop Object")                                 #For debugging
            '''Below section creates a face from the vertices and then extrudes it to create the feature, it then creates a new FreeCAD Part and passes
            the object to the taper function'''
            pts2=[]
            for i in range(0,len(polyLayer)):                                   #Used to create an array of the "Vector points" required in FreeCAD
                pts2.append(FreeCAD.Vector(polyLayer[i][0],polyLayer[i][1],polyLayer[i][2])) #FreeCAD.Vector(x,y,z)
            wire=Part.makePolygon(pts2)                                         #Connects all points given above, makes a wire polygon (just a line)
            face=Part.Face(wire)                                                #Creates a face from the wire above
            if bias != 0:                                                       #If a bias has been given then create a new face
                face = sp.biasFeatures(face, bias)                              #Calls function that biases the feature and returns a new face
            extrusionLIL1.append(face.extrude(Base.Vector(0,0,layer_thickness)))    #Creates an extrusion from the new face
            #Part.show(extrusionLIL1[f])                                        #Used to show the extrusion object - only used for debugging
            #hmedges = extrusionLIL1[f+numOfExt].Edges                          #Finds all the edges, used for debugging
            featureNames.append("myFeature"+str(f+numOfFeatNames))                                                #Creates new feature name
            featureLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", featureNames[f+numOfFeatNames])) #Creates new feature inside FreeCAD
            featureLIL1[f+numOfFeat].Shape = extrusionLIL1[f+numOfExt]                                            #Adds previous extrusion and the feature shape
            print("Before Chamfer")                                             #For debugging
            loop1Break = False; loop2Break = False#; loop3Break = False
            curvedCall = False
            bottomFaces = []
            for face in featureLIL1[-1].Shape.Faces:                                #Searches all the faces in the passed polygon looking for just bottom faces
                for idx, vert in enumerate(face.Vertexes):
                    if idx == (len(face.Vertexes)-1) and round(vert.distToShape(highestObj.Shape)[0],2)==0:  #If the face intersects with the deposition layer then it is at the bottom
                        faceSurface = face.Surface
                        pt=Base.Vector(0,1,0)
                        param = faceSurface.parameter(pt)
                        #print(param)
                        norm = face.normalAt(param[0],param[1])
                        #print(norm)
                        if abs(norm[2]) != 0:                                       #If the face is oriented to one of the sides then ignore it
                            bottomFaces.append(face)                        #Append this face to our list, using list versus fusing them because we want all seperate faces
                            #Part.show(face)                                        #Used for debugging, currently shows the correct bottom faces
                    elif round(vert.distToShape(highestObj.Shape)[0],2)==0 and (round(vert.Point[2],2) >= z_value[-1]):     #If the entire array has not been inspected then inspect next edge
                        continue
                    else:
                        #print("breaking with z value of {:.2f} and height of {:.2f}".format(z_value[-1], vert.Point[2]))   #For debugging
                        break
            for face in bottomFaces:
                for edge1 in face.Edges:#featureLIL1[-1].Shape.Edges:
                    edge1Dir = np.array(edge1.tangentAt(edge1.FirstParameter))      #Finds the vector direction of the edge and converts to a numpy array
                    #Part.show(edge1)
                    for edge2 in face.Edges:#featureLIL1[-1].Shape.Edges:
                        edge2Dir = np.array(edge2.tangentAt(edge2.FirstParameter))  #Finds the vector direction of the edge and converts to a numpy array
                        #Part.show(edge2)
                        #If any of the edges are not at right angles to each other then consider it unable to be chamfered
                        if edge1.firstVertex().Point[2] == edge1.lastVertex().Point[2] == edge2.firstVertex().Point[2] == edge2.lastVertex().Point[2]:
                            cornerAngle = math.degrees(math.acos(np.clip(np.dot(edge1Dir, edge2Dir)/ (np.linalg.norm(edge1Dir)* np.linalg.norm(edge2Dir)), -1, 1)))/90
                            #print(angle)
                            if math.ceil(cornerAngle) != math.floor(cornerAngle):#isinstance(angle, int) == False and angle != 0.0:
                                print("Non-rectangular object found, skipping taper")
                                chamfNames.append("newChamf"+str(len(chamfNames)))                                     #Creates new chamfer name for the fixed object
                                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
                                chamfLIL1[-1].Shape = featureLIL1[-1].Shape
                                #holeSections = chamfLIL1[-1].Shape.cut(polygon.Shape)
                                loop1Break = True; loop2Break = True#; loop3Break = True
                                curvedCall = True
                                break
                        #else:
                        #    print("Continuing")
                    if loop2Break == True:
                        break
                if loop1Break == True:
                    break
            if curvedCall == False:
                taper(featureLIL1[-1], layer_thickness, angle, 0)                   #Passes features to taper function to get tapered, passing 0 for topObj as a placeholder
            else:
                print("Object was Non-rectangular and did not get chamfered")
                #taperNonRectangularObjects(featureLIL1[-1], layer_thickness, angle, highestObj)
            print("After Chamfer")                                              #For debugging
    elif len(FreeCAD.ActiveDocument.Objects) > 1:                               #Already have first layer deposited, these features could be laid on top of previous features
        highestPoint, highestObj = sp.get_highest_point(True,False)             #Finds the highest point and object before the new features are made
        dep_obj = FreeCAD.ActiveDocument.getObject(depositNames[-1])                                #Copies the deposit layer to be used as a "stamp"
        stampObj = FreeCAD.ActiveDocument.addObject("Part::Feature", "myStampingObject")
        stampObj.Shape = dep_obj.Shape
        stampObj.Placement.move(FreeCAD.Vector(0,0,layer_thickness+depositionThickness[-1]))# = p1
        for f in range(0,len(all_polygons_dict[layerNum])):                     #Goes through all polygons in given key (layerNum)
            polyLayer = sp.get_xy_points(all_polygons_dict[layerNum][f])        #Converts all to mm
            for point in polyLayer:
                point.append(z_value[-1])
            print("Before layerDevelop Object")                                 #For debugging
            '''
            The Below section runs through every feature in the layer, creates its object, and extrudes it to the layer thickness + previous deposition thickness
            to account for the need of "stamping" the object to properly layer them. It then moves into creating a stamp from the previous deposition layer
            and moving that stamp and using it to create the proper features (layered if necessary). It then calls the taper function passing it the highest
            object from before the features were created
            '''
            pts2=[]
            for i in range(0,len(polyLayer)):                                                           #Used to create an array of the "Vector points" required in FreeCAD
                pts2.append(FreeCAD.Vector(polyLayer[i][0],polyLayer[i][1],polyLayer[i][2]))            #FreeCAD.Vector(x,y,z)
            wire=Part.makePolygon(pts2)                                                                 #Connects all points given above, makes a wire polygon (just a line)
            face=Part.Face(wire)                                                                        #Creates a face from the wire above
            if bias != 0:                                                       #If a bias has been given then create a new face
                face = sp.biasFeatures(face, bias)                              #Calls function that biases the feature and returns a new face
            extrusionLIL1.append(face.extrude(Base.Vector(0,0,layer_thickness+depositionThickness[-1])))#Creates an extrusion from the new face, needs depositionThickness to get stamped
            #Part.show(extrusionLIL1[f])                                                                #Used to show the extrusion object - only used for debugging
            #hmedges = extrusionLIL1[f+numOfExt].Edges                                                  #Finds all the edges, used for debugging

            cutFeat = FreeCAD.ActiveDocument.addObject("Part::Feature", "myCutObject")                  #Creates a temporary object to hold the cut object, variable reusable
            cutFeat.Shape = extrusionLIL1[-1]#.cut(dep_obj.Shape)                                        #Sets the object to cut as the most recent object extrusion
            for underPoly in lastDeposited:
                cutFeat.Shape = cutFeat.Shape.cut(underPoly.Shape)
            #Below section trims the top with a "stamp"

            #print(stampObj.Base)                                                                       #For debugging
            #p1 = FreeCAD.Placement()
            #p1.move(FreeCAD.Vector(0,0,layer_thickness+depositionThickness[-1]))                       #Moves the stamp upwards by the given amount

            featureNames.append("myFeature"+str(f+numOfFeatNames))                                                #Creates new feature name
            featureLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", featureNames[f+numOfFeatNames])) #Creates new feature inside FreeCAD
            featureLIL1[f+numOfFeat].Shape = cutFeat.Shape.cut(stampObj.Shape)                                    #Adds the feature as the newly "stamped" face
            #Part.show(finalFeat.Shape)
            FreeCAD.ActiveDocument.removeObject("myCutObject")                  #Removes the cut object that is not "stamped" yet

            print("Before Chamfer")                                             #For debugging
            loop1Break = False; loop2Break = False#; loop3Break = False
            curvedCall = False
            bottomFaces = []
            for face in featureLIL1[-1].Shape.Faces:                                #Searches all the faces in the passed polygon looking for just bottom faces
                for idx, vert in enumerate(face.Vertexes):
                    if idx == (len(face.Vertexes)-1) and round(vert.distToShape(highestObj.Shape)[0],2)==0:  #If the face intersects with the deposition layer then it is at the bottom
                        faceSurface = face.Surface
                        pt=Base.Vector(0,1,0)
                        param = faceSurface.parameter(pt)
                        #print(param)
                        norm = face.normalAt(param[0],param[1])
                        #print(norm)
                        if abs(norm[2]) != 0:                                       #If the face is oriented to one of the sides then ignore it
                            bottomFaces.append(face)                        #Append this face to our list, using list versus fusing them because we want all seperate faces
                            #Part.show(face)                                        #Used for debugging, currently shows the correct bottom faces
                    elif round(vert.distToShape(highestObj.Shape)[0],2)==0 and (round(vert.Point[2],2) >= z_value[-1]):     #If the entire array has not been inspected then inspect next edge
                        continue
                    else:
                        #print("breaking with z value of {:.2f} and height of {:.2f}".format(z_value[-1], vert.Point[2]))   #For debugging
                        break
            for face in bottomFaces:
                for edge1 in face.Edges:#featureLIL1[-1].Shape.Edges:
                    edge1Dir = np.array(edge1.tangentAt(edge1.FirstParameter))      #Finds the vector direction of the edge and converts to a numpy array
                    #Part.show(edge1)
                    for edge2 in face.Edges:#featureLIL1[-1].Shape.Edges:
                        edge2Dir = np.array(edge2.tangentAt(edge2.FirstParameter))  #Finds the vector direction of the edge and converts to a numpy array
                        #Part.show(edge2)
                        #If any of the edges are not at right angles to each other then consider it unable to be chamfered
                        if edge1.firstVertex().Point[2] == edge1.lastVertex().Point[2] == edge2.firstVertex().Point[2] == edge2.lastVertex().Point[2]:
                            cornerAngle = math.degrees(math.acos(np.clip(np.dot(edge1Dir, edge2Dir)/ (np.linalg.norm(edge1Dir)* np.linalg.norm(edge2Dir)), -1, 1)))/90
                            #print(angle)
                            if math.ceil(cornerAngle) != math.floor(cornerAngle):#isinstance(angle, int) == False and angle != 0.0:
                                print("Non-rectangular object found, skipping taper")
                                chamfNames.append("newChamf"+str(len(chamfNames)))                                     #Creates new chamfer name for the fixed object
                                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
                                chamfLIL1[-1].Shape = featureLIL1[-1].Shape
                                #holeSections = chamfLIL1[-1].Shape.cut(polygon.Shape)
                                loop1Break = True; loop2Break = True#; loop3Break = True
                                curvedCall = True
                                break
                        #else:
                        #    print("Continuing")
                    if loop2Break == True:
                        break
                if loop1Break == True:
                    break
            if curvedCall == False:
                taper(featureLIL1[-1], layer_thickness, angle, highestObj)          #Calls the taper function passing it the highest object before the new features were made
            else:
                print("Object was Non-rectangular and did not get chamfered")
                #taper(featureLIL1[-1], layer_thickness, angle, highestObj)
                #taperNonRectangularObjects(featureLIL1[-1], layer_thickness, angle, highestObj)
            print("After Chamfer")                                              #For debugging

        FreeCAD.ActiveDocument.removeObject("myStampingObject")             #Removes the stamping surface (previous deposition layer)
    else:
        print("not complete")

    z_value.append(z_value[-1]+layer_thickness)#-.0001)                         #Updates z_value to next height for building onto -*update for uneven features*
    '''
    Below section takes all the newly created chamfered objects and turns them into a single layer, this layer is used in several other functions
    and is the only object displayed in FreeCAD. The other objects get deleted
    '''
    featureCopies = []
    for obj in FreeCAD.ActiveDocument.Objects:                                  #Loops all objects
        if "newChamf" in obj.Label:                                             #If label is not substrate
            featureCopies.append(obj.Shape)                                     #For debugging
    layerCopy = featureCopies[0]                                                #Start out with just the first copied layer
    for feature in featureCopies[1:]:                                           #Add subsequent layers to first copied layer
        layerCopy = layerCopy.fuse(feature)                                     #Fuse combines all features together
    layerNames.append("myLayer"+str(len(layerNames)))                           #Creates new feature name
    layerLIL.append(FreeCAD.ActiveDocument.addObject("Part::Feature", layerNames[-1])) #Creates new feature inside FreeCAD
    layerLIL[-1].Shape = layerCopy                                              #Adds previous extrusion and the feature shape
    lastDeposited.append(layerLIL[-1])                                          #Adds the new layer onto the lastDeposited array, used to keep track of last primary feature
    print("layerDevelop End")                                                   #For debugging
    return layerLIL[-1]


def deposit(all_polygons_dict, sub_layer, dep_thickness):                       #Creates the deposition layer over the existing features
    '''
    deposit function creates a blank deposition of given thickness across all features within the given sub_layer (which should be the substrate layer name).
    It starts by creating a thick (Z value) box that then subtracts out every finalized layer from the layerLIL array. Due to FreeCAD limitations the subtractions
    cannot occur at the same level as the features (FreeCAD cannot display them) so the deposition layer is slightly off (about .5um per layer).

    Function updates the lastDeposited, depositionThickness, layerThickness, and depositLIL arrays.

    Function must be passed the polygon dictionary, the substrate layer, and the desired deposition thickness.

    Returns the final shape of the deposition.
    '''

    print("deposit Begin")                                                      #For debugging

    '''First section here keeps track of the deposition thicknesses, adds a z value to the outer bounds, and then creates the initial box'''
    if dep_thickness > layerThickness[-1]:                                      #If the deposition is thicker than the objects, need to update where the new objects will be placed
        z_value[-1] = z_value[-2] + dep_thickness
    '''if len(depositionThickness) != 0:                   #Used to find the height before the new deposition is made, not currently in use
        preDep = sum(depositionThickness)
    else:
        preDep = 0'''
    depositionThickness.append(dep_thickness)                                   #Adds the newest deposition thickness to check track for comparisons
    #totalDep = sum(depositionThickness)                        #Sums up all the deposition layer thicknesses to shift the deposition layer up by the right amount - not in use currently
    poly_outline = sp.get_xy_points(all_polygons_dict[sub_layer][0])            #Gets the outline of the shape in mm (matches substrate size)
    for i in poly_outline:                                                      #Add the surface of the substrate as bottom of outline points
        i.append(0)#preDep)
    pts=[]
    for i in range(0,len(poly_outline)):                                        #Creates an array of the "vector" points required in FreeCAD
        pts.append(FreeCAD.Vector(poly_outline[i][0],poly_outline[i][1],poly_outline[i][2]))        #FreeCAD.Vector(X,Y,Z)
    wire=Part.makePolygon(pts)                                                  #Creates the edges of the face
    face=Part.Face(wire)                                                        #Create the bottom face
    dep = face.extrude(Base.Vector(0,0,50))                                     #Extrude face a large amount so that it is always above the features (50 here)
    '''
    The contents of the if clause only apply to the first deposition, which is simply removing all the features.
    The contents of the else clause apply to all future depositions, including those over holes, where it deletes everything layer by layer
    to form the final object. In both cases the current features are cut out and then the top is trimmed off with a "stamp" version of the object
    '''
    if len(depositLIL) == 0:
        dep = dep.cut(layerLIL[-1].Shape)                                       #Remove the fused pieces (the features and other deposit layers) from deposit layer
        dep2 = dep.copy()                                                       #Make a copy of dep for the subtraction
        pl = FreeCAD.Placement()                                                #Placement feature for the copied deposit layer
        pl.move(FreeCAD.Vector(0,0,dep_thickness))                              #Moves placement feature up by desired deposit thickness
        dep2.Placement = pl                                                     #This movement up will define the final thickness of the deposit layer
        #Part.show(dep2)                                                        #For debugging
        dep3 = dep.cut(dep2)                                                    #Third layer created that is dep-dep2 leaving only the desired thickness layer with features
        depositNames.append("myDeposit"+str(len(depositNames)))                                 #Creates new internal name for the deposit layer
        depositLIL.append(FreeCAD.ActiveDocument.addObject("Part::Feature", depositNames[-1]))  #Create FreeCAD feature for this deposition
        depositLIL[-1].Shape = dep3                                                             #Sets new deposit shape to desired feature
    else:
        '''Two methods here, either use the uncommented version of the depDelete down to depF = ... or use the commented lines from dep =... to depF = ...'''
        #dep = dep.cut(layerLIL[0].Shape)
        depDelete = lastDeposited[0].Shape                                      #Sets initial shape, required to fuse all objects
        #objC2 = depDelete.copy()
        for idx, obj in enumerate(lastDeposited[1:]):                           #Loops to fuse all objects together, FreeCAD multi-Fuse does not always work
            #print(obj.Label)
            #dep.Placement.move(FreeCAD.Vector(0,0,.0005))
            #dep = dep.cut(obj.Shape)
            #dep.Placement.move(FreeCAD.Vector(0,0,-.0007))
            #dep = dep.cut(obj.Shape).removeSplitter()
            #dep.Placement.move(FreeCAD.Vector(0,0,.0001))

            #objC = obj.Shape.copy()
            #objC.Placement.move(FreeCAD.Vector(0,0,-.0001))
            #objC = objC.cut(objC2).removeSplitter()#lastDeposited[idx].Shape)#.removeSplitter()
            depDelete = depDelete.fuse(obj.Shape).removeSplitter()              #Fuses all objects together and removes any overlapping edges
            #objC2 = obj.Shape.copy()

        #Part.show(depDelete)                                                   #For debugging
        depF = dep.cut(depDelete)                                               #Copies the newly cut object, required for some boolean operations due to FreeCAD (openSCAD maybe)
        #depF = dep.copy()
        #depF.Placement.move(FreeCAD.Vector(0,0,-.0005))
        #Part.show(depF)
        dep2 = depF.copy()                                                      #Make a copy of dep for the subtraction
        pl = FreeCAD.Placement()                                                #Placement feature for the copied deposit layer
        pl.move(FreeCAD.Vector(0,0,dep_thickness))                              #Moves placement feature up by desired deposit thickness
        dep2.Placement = pl                                                     #This movement up will define the final thickness of the deposit layer
        #Part.show(dep2)                                                        #For debugging
        dep3 = depF.cut(dep2)                                                   #Third layer created that is depF-dep2 leaving only the desired thickness layer with features
        depositNames.append("myDeposit"+str(len(depositNames)))                                 #Creates new internal name for the deposit layer
        depositLIL.append(FreeCAD.ActiveDocument.addObject("Part::Feature", depositNames[-1]))  #Create FreeCAD feature for this deposition
        depositLIL[-1].Shape = dep3                                                             #Sets new deposit shape to desired feature
    print("deposit End")                                                        #For debugging
    lastDeposited.append(depositLIL[-1])                                        #Keeps track of all objects layered on "final" device, only finalized objects
    return depositLIL[-1]


#taper does not work with curved objects or objects that appear as curved, not yet at least
def taper(polygon, layer_thickness, angle, topObj):                  #Tapers the edges, passed the surface being projected onto, the object being tapered, and the height
    '''
    taper function takes a given object and chamfers the sides of the object to the specified angle (at max object height). The height chamfered can be adjusted
    by sending the taper function a smaller layer_thickness value. This function is called for all objects being created, even with no chamfer (ease of access).
    Layered objects must be broken down into smaller pieces, one for every face on the bottom of the object; otherwise, FreeCAD cannot chamfer all the outside
    edges of the object.

    This function does not taper objects that interact with holes (vias), see taperOverHoles for that functionality

    This function updates chamfLIL1 and chamfNames arrays

    Passed values are the polygon being chamfered, the z value (height) to chamfer down to (generally the layer thickness of last object, cannot be greater than object height),
    the angle to chamfer it at (0 angle results in no chamfer), and the highest object before the previous features were created

    Returns nothing, all edits done in place
    '''
    numOfExt2 = len(extrusionLIL1)-1                                            #Total number of extrusions, for offsetting, number 2 to ensure they aren't deleted in layerDevelop
    numOfFeat2 = len(featureLIL1)-1                                     #Total number of features, for offsetting, -1 because the feature was added before this length was retrieved
    numOfChamf2 = len(chamfLIL1)                                                #Total number of extrusions, for offsetting
    numOfFeatNames2 = len(featureNames)-1                               #Total number of feature names, for offsetting, -1 because the feature was added before this length was retrieved
    numOfChamfNames2 = len(chamfNames)                                          #Total number of chamfer names, for offsetting

    if angle == 0:                                                              #If no taper is desired or necessary
        chamfNames.append("newChamf"+str(len(chamfNames)))                      #Creates new chamfer name for the fixed object
        chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
        chamfLIL1[-1].Shape = polygon.Shape
    elif len(depositNames) == 0:                                                #If we are chamfering first layer, and there is no deposition layer yet
        chamfNames.append("myChamf"+str(numOfChamfNames2))                                                   #Creates new chamfer name
        chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Chamfer", chamfNames[numOfChamfNames2]))    #Creates new chamfer inside FreeCAD
        chamfLIL1[numOfChamf2].Base = FreeCAD.ActiveDocument.getObject(featureNames[numOfFeatNames2])        #Adds the new feature as the base to chamfer
        '''
        For loop below runs through every face inside the new features and checks its Z values
        If the Z values are equal to the highest Z point then it increments a counter
        If that counter is equal to the number of vertices in that face then it means that every vertex was at the peak point
        So this means the face is the top face. Only works for the first layer. Other layers require more work (other part of if statement)
        '''
        for face in featureLIL1[numOfFeat2].Shape.Faces:                        #Runs through all faces in the newest feature
            count = 0
            for vertex in face.Vertexes:                                        #Extracts each vertex in the face
                if (vertex.Z >= z_value[-1]+layer_thickness-.0001) and \
                    (vertex.Z <= z_value[-1]+layer_thickness+.0001):                     #If the vertex's Z point is equal to the current top location
                    count +=1
            if count == len(face.Vertexes):                                     #If all Vertices have the max z value then this is right face
                foi = face
        #print(foi.Edges[0])                                                    #For debugging
        edgeNums = []; indexing = 0
        '''
        Below loop runs through all of the edges from the previously found top face and adds them to an array
        This loop has to compare the edges of the top face (foi) to the edges of each face in the original object
        This is required to find the index of the face from the original object as it is stored in FreeCAD
        Without doing this the desired edges cannot be selected to use as chamfer edges as it will not edit the original object
        '''
        for edgeMain in featureLIL1[numOfFeat2].Shape.Edges:                    #Runs through all edges in the original shape (the new feature)
            indexing += 1; count = 0
            for edgeFace in foi.Edges:                                          #Runs through each edge in the desired face (top face)
                if edgeMain.firstVertex().Point == edgeFace.firstVertex().Point and edgeMain.lastVertex().Point == edgeFace.lastVertex().Point:
                    edgeNums.append(indexing)                                   #If the start and end vertex of the edges are same then add the index to array
        #print(edgeNums)                                                        #For debugging
        myEdges = []                                                            #Edge array for chamfer function
        for i in range(0, len(edgeNums)):                                       #Runs through all the edges on top face as found from above for loop
            #For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face based off angle)
            #Should be edges 4,7,10,12 for basic features (these are always top edges for a rectangular prism)
            myEdges.append((edgeNums[i],layer_thickness-.0001, layer_thickness*math.tan(angle) )) #Last part was updated to get cut at the desired angle
        chamfLIL1[numOfChamf2].Edges = myEdges                                  #Creates list of all chamfer edges
        FreeCADGui.ActiveDocument.getObject(featureNames[numOfFeatNames2]).Visibility = False #Turns visibility off for unecessary feature (faster run time), object deleted later
        '''
        Below section takes the chamfered objects and shifts it down .0001, then cuts off that .0001 that isn't chamfered at bottom and creates a new
        feature for it. This alleviates the need to do more complicated searches to take the extra .0001 into account, and clears up errors with top edges
        switching directions because of the additional edges at bottom (caused a flip on which way was the Z direction for chamfer.Edges). Deletes the disconnect
        at the .0001 that would otherwise occur in future depositions as well. Ultimately it also cleans up the code, but adds a .1um error to all feature heights.

        **This can potentially change in the future by extruding the object more than its designated thickness and then just cut off the bottom of the feature similar
        to what is being done here, but it would be trimming excess instead of part of the feature itself.
        '''
        FreeCAD.ActiveDocument.recompute()                                      #Recompute is basically reload for FreeCAD, reloads all objects in display
        placement1 = FreeCAD.Placement()                                        #Placement vectors are used to move objects inside FreeCAD
        placement1.move(FreeCAD.Vector(0,0,-.0001))                             #This defines the movement based off created vector
        chamfLIL1[numOfChamf2].Placement = placement1                           #This moves desired object the specificied amount
        newChamf = FreeCAD.ActiveDocument.addObject("Part::Feature", "tempChamf")
        newChamf.Shape = chamfLIL1[numOfChamf2].Shape.cut(FreeCAD.ActiveDocument.getObject("Substrate").Shape) #Cuts the .0001 unchamfered portion on the substrate
        #Need to delete the old chamfer here and add the new one
        FreeCAD.ActiveDocument.removeObject(chamfNames[numOfChamfNames2])       #Deletes the myChamferX object
        chamfNames.pop(numOfChamfNames2)                                        #Removes the myChamferX name
        chamfLIL1.pop(numOfChamf2)                                              #Removes the chamfer object from array
        chamfNames.append("newChamf"+str(numOfChamfNames2))                                                  #Creates new chamfer name for the fixed object
        chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[numOfChamfNames2]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
        chamfLIL1[numOfChamf2].Shape = newChamf.Shape                           #Changes the shape of the previous chamfer to the new chamfer
        FreeCAD.ActiveDocument.removeObject("tempChamf")                        #Deletes the tempChamfX object
    else:
        '''
        Tapering the edges of complex objects is not simply chamfering all the surrounding edges, it involves creating an object for each of the bottom faces
        of the feature. This is due to chamfering of edges overlapping when it is just one feature. So, this portion of the code begins by splitting up the main feature
        into just the bottom faces, if there is only 1 bottom face then the code can do the simple chamfering done above, but if it has multiple bottom faces it will go
        on to create seperate objects and then cut them so they are the right shape for chamfering.It then goes through several ways of finding the outside edges to ensure
        that only the boundary edges are selected before finally chamfering the outside edges.

        There is a chance that the angled faces will protrude past the area of the flat faces, such that cutting them will still leave a portion of the angled
        face that should not be there. One workaround would be to take all the flat faces and extrude them a larger amount and then shift them down after cutting
        the angled faces and shave off that extra extrusion value for the angled objects.
        '''
        bottomFaces = []
        dep_obj2 = FreeCAD.ActiveDocument.getObject(depositNames[-1])           #Copies the deposit layer so that we can check for face comparison
        '''
        Below section gets all the bottom faces of the given feature. It does this by checking to ensure the distance to the layer beneath it is zero
        and then it takes the normal vector of each face and removes all the side faces (either normal in just X or Y direction, no Z component).
        '''
        for face in polygon.Shape.Faces:                                        #Searches all the faces in the passed polygon looking for just bottom faces
            if round(face.distToShape(topObj.Shape)[0],2)==0:                   #If the face intersects with the deposition layer then it is at the bottom
                faceSurface = face.Surface                                      #Grabs the surface object of the face
                pt=Base.Vector(0,1,0)
                param = faceSurface.parameter(pt)                               #Finds the parameters associated between the vector and surface
                #print(param)                                                   #For debugging
                norm = face.normalAt(param[0],param[1])                         #Returns the normal for the given point, based off previous parameters
                #print(norm)                                                    #For debugging
                if abs(norm[0]) != 1 and abs(norm[1]) != 1:                     #If the face is oriented to one of the sides (something that is unwanted)
                    bottomFaces.append(face)                                    #Append this face to our list, using list versus fusing them because we want all seperate faces
                    #Part.show(face)                                            #Used for debugging, currently shows the correct bottom faces
        if len(bottomFaces) == 0:                                               #If it cannot find any bottom faces, this means the object is floating or has an error
            bad = FreeCAD.ActiveDocument.addObject("Part::Feature", "BreakingStuff")    #Used to debug the feature at which the chamfering stopped working
            bad.Shape = polygon
            print("What is this shape?")                                        #Placeholder
        elif len(bottomFaces) == 1:                                             #Only 1 bottom face, so it is not layered on top of any other features
            '''
            This portion of the code is nearly identical to the top portion of the outside if statement, only small adjustments. Initial portion creates a temporary object
            required to properly set the chamfer base equal to (FreeCAD requirement).
            '''
            #Part.show(polygon)                                                 #For debugging
            tempObj = bottomFaces[0].extrude(Base.Vector(0,0,layer_thickness))  #Initial extrusion
            polyFeature = FreeCAD.ActiveDocument.addObject("Part::Feature", "SillyName"+str(len(chamfNames))) #Must create this to set chamfer base equal to, SillyName is placeholder
            polyFeature.Shape = tempObj
            chamfNames.append("myChamf"+str(len(chamfNames)))                                                 #Creates new chamfer name, 0 is f is layerDevelop
            chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Chamfer", chamfNames[-1]))               #Creates new chamfer inside FreeCAD, 0 should be number of features up to here, used as f above
            chamfLIL1[-1].Base = polyFeature                                    #Adds the new feature as the base to chamfer
            '''
            For loop below runs through every face inside the new features and checks its Z values
            If the Z values are equal to the highest Z point then it increments a counter
            If that counter is equal to the number of vertices in that face then it means that every vertex was at the peak point
            So this means the face is the top face. Only works for the first layer. Other layers require more work (other part of if statement)
            '''
            for face in polyFeature.Shape.Faces:                                #Runs through all faces in the newest feature
                count = 0
                for vertex in face.Vertexes:                                    #Extracts each vertex in the face
                    if vertex.Z >= z_value[-1]+layer_thickness:                 #If the vertex's Z point is equal to the current top location
                        count +=1
                if count == len(face.Vertexes):                                 #If all Vertices have the max z value then this is right face
                    foi = face
            #print(foi.Edges[0])                                                #For debugging
            edgeNums = []; indexing = 0
            '''
            Below loop runs through all of the edges from the previously found top face and adds them to an array
            This loop has to compare the edges of the top face (foi) to the edges of each face in the original object
            This is required to find the index of the face from the original object as it is stored in FreeCAD
            Without doing this the desired edges cannot be selected to use as chamfer edges as it will not edit the original object.
            '''
            for edgeMain in polyFeature.Shape.Edges:                            #Runs through all edges in the original shape (the new feature)
                indexing += 1; count = 0
                for edgeFace in foi.Edges:                                      #Runs through each edge in the desired face (top face)
                    if edgeMain.firstVertex().Point == edgeFace.firstVertex().Point and edgeMain.lastVertex().Point == edgeFace.lastVertex().Point:
                        edgeNums.append(indexing)                               #If the start and end vertex of the edges are same then add the index to array
                        break
            #print(edgeNums)                                                    #For debugging
            myEdges = []                                                        #Edge array for chamfer function
            for i in range(0, len(edgeNums)):                                   #Runs through all the edges on top face as found from above for loop
                #For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face)
                #Should be edges 4,7,10,12 for basic features (these are always top edges for a rectangular prism)
                myEdges.append((edgeNums[i],layer_thickness-.0001, layer_thickness*math.tan(angle) )) #Last part was updated to get cut at the desired angle
            chamfLIL1[-1].Edges = myEdges                                       #Creates list of all chamfer edges
            '''
            Below section takes the chamfered objects and shifts it down .0001, then cuts off that .0001 that isn't chamfered at bottom and creates a new
            feature for it. This alleviates the need to do more complicated searches to take the extra .0001 into account, and clears up errors with top edges
            switching directions because of the additional edges at bottom (caused a flip on which way was the Z direction for chamfer.Edges). Deletes the disconnect
            at the .0001 that would otherwise occur in future depositions as well. Ultimately it also cleans up the code, but adds a .1um error to all feature heights.

            **This can potentially change in the future by extruding the object more than its designated thickness and then just cut off the bottom of the feature similar
            to what is being done here, but it would be trimming excess instead of part of the feature itself.
            '''
            FreeCAD.ActiveDocument.recompute()                                  #Recompute is basically reload for FreeCAD, reloads all objects in display
            placement1 = FreeCAD.Placement()                                    #Placement vectors are used to move objects inside FreeCAD
            placement1.move(FreeCAD.Vector(0,0,-.0001))		                    #This defines the movement based off created vector
            chamfLIL1[-1].Placement = placement1                                #This moves desired object the specificied amount
            newChamf = FreeCAD.ActiveDocument.addObject("Part::Feature", "tempChamf")
            newChamf.Shape = chamfLIL1[-1].Shape.cut(FreeCAD.ActiveDocument.getObject(depositNames[-1]).Shape) #Cuts the .0001 unchamfered portion on the deposition layer
            #Need to delete the old chamfer here and add the new one
            FreeCAD.ActiveDocument.removeObject(chamfNames[-1])                 #Deletes the myChamferX object
            chamfNames.pop()                                                    #Removes the myChamferX name
            chamfLIL1.pop()                                                     #Remvoes the chamfer object from array
            chamfNames.append("newChamf"+str(len(chamfNames)))                  #Creates new chamfer name for the fixed object
            chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
            chamfLIL1[-1].Shape = newChamf.Shape                                #Sets chamfer object base to the newChamf object
            FreeCAD.ActiveDocument.removeObject("tempChamf")                    #Deletes the tempChamfX object
        else:                                                                   #More than one face, so on top of another features
            '''
            This section of the if statement catches any objects that are layered on top of another previously created object. It presumes the object below it
            has also been chamfered, and might not worked if it has not been chamfered (untested at this time).

            The first section takes all the bottom faces of the passed polygon and extrudes them by the desired amount (creating FreeCAD objects for each, required
            for chamfering). It then goes through and trims off the excess edges of all the objects that forms from the angled objects, creating a new list
            of cleaned objects.'''
            separateObjNames = []                                               #Used to declare names for each object feature
            separateObj = []                                                    #Used to hold all the separated objects
            for counter,face in enumerate(bottomFaces):                         #Runs through all the bottom faces to create objects from them
                tempObj = face.extrude(Base.Vector(0,0,layer_thickness))        #Initial extrusion
                separateObjNames.append("tempObj" + str(counter))               #Creates a name for the objects
                separateObj.append(FreeCAD.ActiveDocument.addObject("Part::Feature", separateObjNames[-1])) #Creates FreeCAD features for each of the objects
                separateObj[-1].Shape = tempObj                                 #Initializes the feature shape to that of the initial extrusion
                FreeCADGui.ActiveDocument.getObject(separateObjNames[-1]).Visibility = False #Will need to delete them later
            cleanedSeparateObj = []                                             #Used to store all the separate objects after they have been cut
            for outer, extrusion in enumerate(separateObj):                     #For all the shapes subtract out every other shape
                noObj = True                                                    #Used to tell if there is an object on the first outershell section
                for inner,otherExtrusions in enumerate(separateObj):            #Fuse together all objects that are not being inspected, used for 1 cut operation
                    if outer==inner:                                            #If we are looking at the same object
                        continue                                                #Skip this object
                    elif noObj:                                                 #First loop through, set the tempObj equal to the otherExtrusions
                        noObj = False                                           #If there has been no object added yet
                        tempObj2 = otherExtrusions.Shape
                    else:                                                       #Fuses all aditional objects
                        tempObj2 = tempObj2.fuse(otherExtrusions.Shape)
                #Part.show(tempObj2)                                            #Used to debug if all the objects fused properly
                cleanedSeparateObj.append(extrusion.Shape.cut(tempObj2))        #Appends the newly cut objects to the array (as Shapes)
                #Part.show(cleanedSeparateObj[-1])                              #Used to verify that the object was cut correctly
            '''
            Now all the objects are created, so need to find all the correct edges and chamfer them.
            Below section is designed to to get rid of the bottom and side faces of our object, so that only the top edges are considered.
            It starts by verifying the normal has a Z component (deletes side faces), it then checks to ensure that all edges are not touching the
            layer the feature was created on top off. Lastly it checks to ensure that the raised sections that still touch the deposit layer
            is deleted.

            **This could likely be increased in speed by checking the distance to the deposit layer and veryfying it is greater than zero.
            '''
            finalPolygonArray = []                                              #Will hold all the chamfered polygons
            faceToInspect = []
            for face in polygon.Shape.Faces:                                    #This loop gets rid of all the side faces
                faceSurface = face.Surface
                pt=Base.Vector(0,1,0)
                param = faceSurface.parameter(pt)
                #print(param)
                norm = face.normalAt(param[0],param[1])
                #print(norm)
                if abs(norm[2]) > 0 :                                           #If the face has a Z component in its normal
                    for edge in face.Edges: #This loop makes sure all the edges are on top, so deletes bottom faces, except the ones raised on top of another feature (deleted after)
                        if edge.firstVertex().Point[2] >= layer_thickness+depositionThickness[-1] and edge.lastVertex().Point[2] >= layer_thickness+depositionThickness[-1]:
                            faceToInspect.append(face)                          #Keeps track of all the faces that edges are needed from
                            break                                               #If face is added, break out of the for loop so it doesn't get added again
            breakLoop = 0                                                       #break counter for following loops
            faceRemovalArray = []                                               #Keeps track of the indices that need to be removed from the faceToInspect array
            #Can maybe make below loops faster by just checking the distance from the faces to the dep layer, versus all this mayhem
            dep_obj2 = FreeCAD.ActiveDocument.getObject(depositNames[-1])       #Copies the deposit layer to check for face comparison
            for i in range(0,len(faceToInspect)):               #For all newly added faces, compare vertices to vertices of the last deposit layer, if they match then remove the face
                #This will get rid of the faces that are at the required height, but touching the deposit layer, i.e. on top of features
                for edge in faceToInspect[i].Edges:
                    for eoi in dep_obj2.Shape.Edges:                            #Grabs all vertices from previous deposition layer
                        if edge.firstVertex().Point[2] == eoi.firstVertex().Point[2] or edge.lastVertex().Point[2] == eoi.lastVertex().Point[2]:
                            if edge.firstVertex().Point[0] == eoi.firstVertex().Point[0] or edge.firstVertex().Point[1] == eoi.firstVertex().Point[1]:
                                #print(edge.distToShape(dep_obj.Shape))         #For debugging
                                if edge.distToShape(dep_obj2.Shape)[0] == 0:
                                    faceRemovalArray.append(i)                  #Tracks the face that matches vertices with the deposition layer
                                    breakLoop += 1                              #If this increments need to stop comparing edges and break the second loop too
                                    break                                       #Breaks out of third for loop
                    if breakLoop == 1:
                        breakLoop = 0
                        break                                                   #Breaks out of second for loop
            #print(faceRemovalArray)                                            #Prints all face indicies that need to get removed, for debugging
            for rem in sorted(faceRemovalArray, reverse=True):                  #Deletes the indicies in reverse to not mess up the index order
                del faceToInspect[rem]                                          #Removes the edges on top of the features
            '''
            Below section takes the top faces and finds all the edges that need to be chamfered from it. First it creates a shell, which is one object
            of all the faces, then it finds the outside boundary wires of that shell. This technically creates a single object from all the previously separated
            objects, it is again seperated in the following for loop.
            '''
            new_obj=FreeCAD.ActiveDocument.addObject("Part::Feature","NewObj") #new object used as a shell to search for all the edges, variable resuable
            new_obj = Part.makeShell(faceToInspect) #use Part.Shell not Part.Compound as Part.Compound does only generic grouping
            #new_obj.removeSplitter()
            boundary = []       #Finds a boundary list for all the outside edges, this might be the only thing we need now?
            for face in new_obj.Faces:
                for edge in face.OuterWire.Edges:
                    ancestors = new_obj.ancestorsOfType(edge, Part.Face)
                    if len(ancestors) == 1:
                        boundary.append(edge)
                        #Part.show(edge)
            edgeList = boundary                                                 #Edge list to how all the edges needed for the chamfer
            '''#The following 3 lines are used for debugging, to ensure the proper boundary edges were found
            tempWire = Part.makePolygon(edgeList)
            tempFace = Part.Face(tempWire)
            Part.show(tempFace)'''

            '''
            Below for loop runs through every face (all top faces) of the new objects and finds the desired edges from the original object needed to chamfer.
            For some reason there is a blank object at end of the cleanedSeparateObj list, or at least it shows up while trying to chamfer.

            ** Could part of this be taken out to increase running speed?
            '''
            for counter, polyShape in enumerate(cleanedSeparateObj):            #Takes each object from the new objects array
                #Part.show(polyShape)                                           #For debugging
                print("At start of object separation")
                for face in polyShape.Faces:                                    #Inspects individual faces from the shapes, if they are not touching the object below, then inspect them
                    if face.distToShape(topObj.Shape)[0] > .1:
                        faceToInspect2 = face
                        #Part.show(face)                                        #For debugging
                        break
                #print("Number of faces in faceToInspect" + str(faceToInspect2)) #For debugging, should only be 1 edge
                '''
                Below section takes the boundary wires of all the new objects and compares them to the edges of the oringinal feature, the edge number (index) of
                the original feature is then recorded. This is important because edge numbers are generated uniquely and so the new objects do not share the edge numbers
                of the original feature.

                edgeList contains the edges of the main shape, faceToInspect2 is the top face of the new object, and edgeList 2 will hold the edges needed for the final
                comparison.

                **After fixing the issue with FreeCAD not being able to chamfer the entire height of an object, part of the following might be able to be removed.
                '''
                edgeList2 = []                                                  #Edge list of all the edges needed for the chamfer
                for counterT, edgeToAdd in enumerate(faceToInspect2.Edges):     #Checks every edge in boundary array to ensure they are not between two faces (only true boundary edges)
                    for counter3,edgeExists in enumerate(edgeList):             #Runs through every edge currently in edgeList, comparing to the newly added edge
                        toAddX1 = round(edgeToAdd.firstVertex().Point[0],2); toAddY1 = round(edgeToAdd.firstVertex().Point[1],2); toAddZ1 = round(edgeToAdd.firstVertex().Point[2],2)
                        existsX1 = round(edgeExists.firstVertex().Point[0],2); existsY1 = round(edgeExists.firstVertex().Point[1],2); existsZ1 = round(edgeExists.firstVertex().Point[2],2)
                        toAddX2 = round(edgeToAdd.lastVertex().Point[0],2); toAddY2 = round(edgeToAdd.lastVertex().Point[1],2); toAddZ2 = round(edgeToAdd.lastVertex().Point[2],2)
                        existsX2 = round(edgeExists.lastVertex().Point[0],2); existsY2 = round(edgeExists.lastVertex().Point[1],2); existsZ2 = round(edgeExists.lastVertex().Point[2],2)
                        '''#For debugging
                        print("ToAdd1")
                        print(toAddX1,toAddY1,toAddZ1)
                        print(existsX1,existsY1,existsZ1)
                        print("ToAdd2")
                        print(toAddX2,toAddY2,toAddZ2)
                        print(existsX2,existsY2,existsZ2)'''

                        '''
                        Because new objects were created to separate out the edges for chamfering some of the edges might not be going in the same direction
                        For example, one edge that might be shared (the same edge) could actually have firstVertex and lastVertex flipped
                        This is normally not the case after fixing the subtraction issue with not chamfering the entire object height, but if this error does occur
                        it can be fixed by using the __sortEdges__ (function call might be mispelled) function for FreeCAD .19 and later

                        **Might be able to remove the below if statement
                        '''
                        if (toAddX1 == existsX1 or toAddX1 == existsX2) and (toAddY1 == existsY1 or toAddY1 == existsY2) and \
                        (toAddZ1 == existsZ1 or toAddZ1 == existsZ2) and (toAddX2 == existsX2 or toAddX2 == existsX1) and \
                        (toAddY2 == existsY2 or toAddY2 == existsY1) and (toAddZ2 == existsZ2 or toAddZ2 == existsZ1): #This accounts for the .0001 difference when comparing them
                            ''' For debugging
                            print("ToAdd1")
                            print(toAddX1,toAddY1,toAddZ1)
                            print(existsX1,existsY1,existsZ1)
                            print("ToAdd2")
                            print(toAddX2,toAddY2,toAddZ2)
                            print(existsX2,existsY2,existsZ2)'''
                            #print("Edge Equal")                                #For debugging
                            edgeList2.append(edgeToAdd)                         #Keeps track of all the edges that need to get chamfered
                            break                                               #This keeps the edge from being added multiple times
                #newWire2 = edgeList2[0].multiFuse(edgeList2[1:])               #Creates a wire for debugging
                #Part.show(newWire2)                                            #Used for debugging, show all the final edges on the top boundary
                '''
                Below section takes the newly found edges and compares them to the original object. It takes the index of the original object's edges
                that are equal to the edges in the edgeList2 and uses those to create the chamfer edges. It then chamfers the objects to the specified angle
                and cleans up. Chamfers for angled objects are more complex and the actual height of that object will depend on the angle and thickness
                of the object it is layered on top of. To get around this the height of the angle objects is found and then inserted into the chamfer height.
                '''
                print("After edge selection")
                polyFeature = FreeCAD.ActiveDocument.addObject("Part::Feature", "SillyName"+str(counter))                    #Must create this to set chamfer base equal to
                polyFeature.Shape = polyShape
                chamfNames.append("myChamf"+str(counter+numOfChamfNames2))                                                   #Creates new chamfer name, 0 is f is layerDevelop
                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Chamfer", chamfNames[counter+numOfChamfNames2]))    #Creates new chamfer inside FreeCAD, 0 should be number of features up to here, used as f above
                chamfLIL1[counter+numOfChamf2].Base = polyFeature               #Adds the new feature as the base to chamfer
                edgeNums = []
                indexing = 0
                #tempArr4 = [3,33]                                              #Used for debugging which edges do not chamfer properly
                for edgeMain in polyShape.Edges:                                #Runs through all edges in the original shape (the new feature)
                    indexing += 1; count = 0
                    for edgeFace in edgeList2:                                  #Runs through each edge in the desired face (top face)
                        if edgeMain.firstVertex().Point == edgeFace.firstVertex().Point and edgeMain.lastVertex().Point == edgeFace.lastVertex().Point:
                            edgeNums.append(indexing)                           #If the start and end vertex of the edges are same then add the index to array
                            break
                #print(edgeNums)                                                #For debugging
                print("After edge indexing ")
                #edgeNums = list(set(edgeNums))                                 #For some reason, sometimes one edge gets added to this multiple times, so this gives only unique numbers
                #tempedgeNums = [4,10]                                          #Used for debugging which edges do not chamfer properly
                #print(edgeList2)                                               #For debugging
                '''
                Below section adds the chamfer edges to the chamfer list along with the amount to chamfer. Due to quirks in FreeCAD the amount needed to chamfer the entire
                height of the object will vary depending on if it is flat or angled. The first section below finds the tangent to test if the object is flat or angled (on top of
                another feature). The flat objects are straightforward with the amount needed to chamfer simply being the thickness of the object. The angled features vary depending
                on the chamfer and and the angle of the feature it is laid on top of. This problem is solved by finding the height of the angled object in relation to the deposition
                layer below it and then taking an adjusted amount off from there: the .00002 allows objects angled from 5 to 65 to be chamfered properly. Larger angles can have
                more unchamfered (i.e. .0001), but smaller angles require less left behind which is then subtracted out when making "newChamf" Features.

                **Might need to sort edges before chamfering depending on how the cut feature creates the new objects, but generally this should not be the case (debug this later).
                '''
                flat = False
                myEdges = []                                                    #Edge array for chamfer function
                for face in polyShape.Faces:                                    #Searches all the faces in the passed polygon looking for just bottom faces
                    if face.distToShape(dep_obj2.Shape)[0] == 0:                #If the face intersects with the deposition layer then it is at the bottom
                        faceSurface = face.Surface
                        pt=Base.Vector(0,1,0)
                        param = faceSurface.parameter(pt)
                        norm = face.normalAt(param[0],param[1])
                        if abs(norm[2]) == 1:                                   #If the face is oriented to one of the sides, not a bottom face
                            flat = True                                         #This means the object is not layered on another feature (not angled)
                if flat:                                                        #Objects that are not angled
                    for i in edgeNums:                                          #Runs through all the edges on top face as found from above for loop
                        #For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face (set at the desired angle))
                        myEdges.append((i,layer_thickness-.0001,layer_thickness*math.tan(angle) ))
                        #print(i)                                               #Prints edge index, for debugging
                else:                                                           #If the object is layered on top of another object (angled)
                    angHeight = edgeList2[0].firstVertex().distToShape(dep_obj2.Shape)[0] #Gets distance from the top edge to the deposition layer
                    for i in edgeNums:                                          #Runs through all the edges on top face as found from above for loop
                        '''
                        For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face (set at the desired angle))
                        For some reason the angled features are not as thick as the regular ones. For a layer_thickness of 1, the angled features
                        only have a thickness of .85099, so about 85.099% as thick.
                        For angled objects, the amount needed to chamfer the Z portion will vary depending on the angle of the features below it
                        and its own angle and sometimes on the thickness
                        '''
                        myEdges.append((i,(angHeight)-.00002,layer_thickness*math.tan(angle)))
                        #print(i)                                               #Prints edge index, for debugging
                chamfLIL1[counter+numOfChamf2].Edges = myEdges                  #Creates list of all chamfer edges
                FreeCAD.ActiveDocument.recompute()                              #Recompute is basically reload for FreeCAD, reloads all objects in display
                finalPolygonArray.append(chamfLIL1[-1].Shape)                   #Holds all the chamfered shapes
                FreeCADGui.ActiveDocument.getObject(polyFeature.Label).Visibility = False
                '''
                Below section takes the chamfered objects and shifts it down .0001, then cuts off that .0001 that isn't chamfered at bottom and creates a new
                feature for it. Experimenting with this to see if it will alleviate the need for the complicated searches above, and clear up the incorrect directions
                of edges that occur when there is a disconnect from the .0001 distance. So it should fix the disconnect of edges and clean up the code. It does these nicely
                but causes an offset in each layer that stacks up over time. Eventually if there are enough layers this can cause a small breakdown in the code. Generally
                the deposition layer should take care of some of this, but ultimately this will need to get fixed.

                **One method that could fix this is increasing the initial extrusion and then chamfering just the layer thickness amount before cutting off that extra extrusion
                value
                '''
                placement1 = FreeCAD.Placement()                                #Placement vectors are used to move objects inside FreeCAD
                placement1.move(FreeCAD.Vector(0,0,-.0001))		                #This defines the movement based off created vector
                chamfLIL1[-1].Placement = placement1                            #This moves desired object the specificied amount
                newChamf = FreeCAD.ActiveDocument.addObject("Part::Feature", "tempChamf")
                newChamf.Shape = chamfLIL1[-1].Shape.cut(topObj.Shape)          #Cuts the .0001 unchamfered portion on the deposition layer
                #Need to delete the old chamfer here and add the new one
                FreeCAD.ActiveDocument.removeObject(chamfNames[-1])             #Deletes the myChamferX object
                chamfNames.pop()                                                #Removes the myChamferX name
                chamfLIL1.pop()                                                 #Removes the chamfer object from array
                chamfNames.append("newChamf"+str(numOfChamfNames2+counter))     #Creates new chamfer name for the fixed object
                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
                chamfLIL1[-1].Shape = newChamf.Shape
                FreeCAD.ActiveDocument.removeObject("tempChamf")                #Deletes the tempChamf object object
                print("After obj chamfer")

#taperOverHoles does not work with curved objects or objects that appear as curved, not yet at least
def taperOverHoles(polygon, layer_thickness, angle, topObj):
    '''
    taperOverHoles function takes a given object and chamfers the sides of the object to the specified angle (at max object height). The height chamfered can be adjusted
    by sending the taper function a smaller layer_thickness value. This function is called for all objects being created, even with no chamfer (ease of access).
    Layered objects must be broken down into smaller pieces, one for every face on the bottom of the object; otherwise, FreeCAD cannot chamfer all the outside
    edges of the object.

    This function is designed for layer that interact with vias, for regular tapering see the taper function

    This function updates chamfLIL1 and chamfNames arrays

    Passed values are the polygon being chamfered, the z value (height) to chamfer down to (generally the layer thickness of last object, cannot be greater than object height),
    the angle to chamfer it at (0 angle results in no chamfer), and the highest object before the previous features were created

    Returns nothing, all edits done in place
    '''
    print("taperOverHoles begin")
    numOfExt2 = len(extrusionLIL1)-1                                            #Total number of extrusions, for offsetting, number 2 to ensure they aren't deleted in layerDevelop
    numOfFeat2 = len(featureLIL1)-1                                     #Total number of features, for offsetting, -1 because the feature was added before this length was retrieved
    numOfChamf2 = len(chamfLIL1)                                                #Total number of extrusions, for offsetting
    numOfFeatNames2 = len(featureNames)-1                               #Total number of feature names, for offsetting, -1 because the feature was added before this length was retrieved
    numOfChamfNames2 = len(chamfNames)                                          #Total number of chamfer names, for offsetting
    #print(angle)
    if angle != 0:                                                              #If there is a chamfer angle given
        '''
        Need to create a section here that takes our object and splits it apart where each bottom face is an object. Then I need to extrude those faces
        by the desired amount and cut off the intersection with all the other faces (such that the angled face extrusions will not be inside of the flat ones).
        Then I need to chamfer the desired edges before reconnecting all the individual objects back together.

        There is a chance that the angled faces will protrude past the area of the flat faces, such that cutting them will still leave a portion of the angled
        face that should not be there. One workaround would be to take all the flat faces and extrude them a larger amount and then shift them down after cutting
        the angled faces and shave off that extra extrusion value.
        '''
        bottomFaces = []
        dep_obj2 = FreeCAD.ActiveDocument.getObject(lastDeposited[-1].Label).Shape.copy()      #Copies the deposit layer to check for face comparison
        #Part.show(dep_obj2)
        #Part.show(topObj.Shape)
        #print("Debugger")
        '''Below section also grabs the side faces to remove them'''
        for face in polygon.Shape.Faces:                                        #Searches all the faces in the passed polygon looking for just bottom faces
            #print("Debugger 2")
            for idx, vert in enumerate(face.Vertexes):
                #print("Debugger 3")
                if idx == (len(face.Vertexes)-1) and round(vert.distToShape(topObj.Shape)[0],2)==0:  #If the face intersects with the deposition layer then it is at the bottom
                    #print("Debugger 4")
                    faceSurface = face.Surface
                    pt=Base.Vector(0,1,0)
                    param = faceSurface.parameter(pt)
                    #print(param)
                    norm = face.normalAt(param[0],param[1])
                    #print(norm)
                    if abs(norm[2]) != 0:                                       #If the face is oriented to one of the sides then ignore it
                        bottomFaces.append(face)                                #Append face to list, using list versus fusing them as need to be all seperate faces
                        #Part.show(face)                                        #Used for debugging, currently shows the correct bottom faces
                elif round(vert.distToShape(topObj.Shape)[0],2)==0 and (round(vert.Point[2],2) >= z_value[-1]):     #If the entire array has not been inspected then inspect next edge
                    continue
                else:
                    #print("breaking with z value of {:.2f} and height of {:.2f}".format(z_value[-1], vert.Point[2]))   #For debugging
                    break
        #print(len(bottomFaces))                                                 #For debugging
        '''
        If there are no bottom faces then there is a floating object or object missing, so the code throws an error. Otherwise, if there is 1 bottom face
        then do basic calculations not worrying about angled objects (layered on not of other objects). If there are multiple bottom faces then it is likely layered
        on top of another object and requires more work to find the correct edges to chamfer.

        **There might not be a need for special case 2 bottom faces
        '''
        if len(bottomFaces) == 0:                                               #This means there is an invalid object being passed
            bad = FreeCAD.ActiveDocument.addObject("Part::Feature", "BreakingStuff")    #Placeholder to show that there is an invalid object in taper
            bad.Shape = polygon
            print("What is this shape?")                                        #For debugging
        elif len(bottomFaces) == 1: #Only 1 bottom face, so it is not going over any other features
            #Part.show(polygon)                                                 #For debugging
            tempObj = bottomFaces[0].extrude(Base.Vector(0,0,layer_thickness))  #Initial extrusion
            #Part.show(tempObj)                                                 #For debugging
            print("Only 1 bottom face found")
            originalObj = polygon.Shape.copy()                                  #Copy of the original polygon, used for cuts and comparisons
            justHoles = originalObj.cut(tempObj)                                #Removes the hole section from the main object, so it is not inspected
            holeSections = justHoles                                            #Copy of the hole section, used for object naming after chamfer is complete
            if len(justHoles.Faces) == 0:                                       #No holes on this feature - should work as regular chamfer
                print("No holes present inside taper function")
                polyFeature = FreeCAD.ActiveDocument.addObject("Part::Feature", "SillyName"+str(len(chamfNames)))   #Must create this to set chamfer base equal to
                polyFeature.Shape = tempObj
                chamfNames.append("myChamf"+str(len(chamfNames)))                                                   #Creates new chamfer name
                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Chamfer", chamfNames[-1]))                 #Creates new chamfer inside FreeCAD
                chamfLIL1[-1].Base = polyFeature                                #Adds the new feature as the base to chamfer
                '''
                For loop below runs through every face inside the new features and checks its Z values
                If the Z values are equal to the highest Z point then it increments a counter
                If that counter is equal to the number of vertices in that face then it means that every vertex was at the peak point
                So this means the face is the top face. Only works for the first layer. Other layers require more work (other part of if statement)
                '''
                for face in polyFeature.Shape.Faces:                            #Runs through all faces in the newest feature
                    count = 0
                    for vertex in face.Vertexes:                                #Extracts each vertex in the face
                        if vertex.Z >= z_value[-1]+layer_thickness-.0005:       #If the vertex's Z point is equal to the current top location (or close to it)
                            count +=1
                    if count == len(face.Vertexes):                             #If all Vertices have the max z value then this is right face
                        foi = face
                #print(foi.Edges[0])                                            #For debugging
                '''
                Below loop runs through all of the edges from the previously found top face and adds them to an array
                This loop has to compare the edges of the top face (foi) to the edges of each face in the original object
                This is required to find the index of the face from the original object as it is stored in FreeCAD
                Without doing this the desired edges cannot be selected to use as chamfer edges as it will not edit the original object
                '''
                edgeNums = []; indexing = 0
                for edgeMain in polyFeature.Shape.Edges:           #Runs through all edges in the original shape (the new feature)
                    indexing += 1; count = 0
                    for edgeFace in foi.Edges:                                  #Runs through each edge in the desired face (top face)
                        if edgeMain.firstVertex().Point == edgeFace.firstVertex().Point and edgeMain.lastVertex().Point == edgeFace.lastVertex().Point:
                            edgeNums.append(indexing)                           #If the start and end vertex of the edges are same then add the index to array
                            break
                #print(edgeNums)                                                #For debugging
                myEdges = []                                                    #Edge array for chamfer function
                for i in range(0, len(edgeNums)):                               #Runs through all the edges on top face as found from above for loop
                    #For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face *Needs to be the angle*)
                    #Should be edges 4,7,10,12 for basic features (these are always top edges for a rectangular prism)
                    myEdges.append((edgeNums[i],layer_thickness-.0001, layer_thickness*math.tan(angle) )) #Last part was updated to get cut at the desired angle
                chamfLIL1[-1].Edges = myEdges                                    #Creates list of all chamfer edges
                #FreeCADGui.ActiveDocument.getObject(featureNames[-1]).Visibility = False #Does this need FreeCADGui or FreeCAD as leader?
                '''
                Below section takes the chamfered objects and shifts it down .0001, then cuts off that .0001 that isn't chamfered at bottom and creates a new
                feature for it. This alleviates the need to do more complicated searches to take the extra .0001 into account, and clears up errors with top edges
                switching directions because of the additional edges at bottom (caused a flip on which way was the Z direction for chamfer.Edges). Deletes the disconnect
                at the .0001 that would otherwise occur in future depositions as well. Ultimately it also cleans up the code, but adds a .1um error to all feature heights.

                **This can potentially change in the future by extruding the object more than its designated thickness and then just cut off the bottom of the
                feature similar to what is being done here, but it would be trimming excess instead of part of the feature itself.
                '''

                FreeCAD.ActiveDocument.recompute()                              #Recompute is basically reload for FreeCAD, reloads all objects in display
                placement1 = FreeCAD.Placement()                                #Placement vectors are used to move objects inside FreeCAD
                placement1.move(FreeCAD.Vector(0,0,-.0001))		                #This defines the movement based off created vector
                chamfLIL1[-1].Placement = placement1                            #This moves desired object the specificied amount
                newChamf = FreeCAD.ActiveDocument.addObject("Part::Feature", "tempChamf")
                newChamf.Shape = chamfLIL1[-1].Shape.cut(topObj.Shape)          #Cuts the .0001 unchamfered portion on the deposition layer
                #Need to delete the old chamfer here and add the new one
                FreeCAD.ActiveDocument.removeObject(chamfNames[-1])             #Deletes the myChamferX object
                chamfNames.pop()                                                #Deletes the myChamferX name
                chamfLIL1.pop()                                                 #Removes the chamfer object from array
                chamfNames.append("newChamf"+str(len(chamfNames)))              #Creates new chamfer name for the fixed object
                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
                chamfLIL1[-1].Shape = newChamf.Shape
                FreeCAD.ActiveDocument.removeObject("tempChamf")                #Deletes the tempChamf object
                print("After obj chamfer")
            else:
                print("Holes found within layer")
                polyFeature = FreeCAD.ActiveDocument.addObject("Part::Feature", "SillyName"+str(len(chamfNames))) #Must create this to set chamfer base equal to
                polyFeature.Shape = tempObj                                                                       #Sets shape equal to the extruded face
                chamfNames.append("myChamf"+str(len(chamfNames)))                                                 #Creates new chamfer name
                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Chamfer", chamfNames[-1]))               #Creates new chamfer inside FreeCAD
                chamfLIL1[-1].Base = polyFeature                                #Adds the new feature as the base to chamfer
                '''
                For loop below runs through every face inside the new features and checks its Z values
                If the Z values are equal to the highest Z point then it increments a counter
                If that counter is equal to the number of vertices in that face then it means that every vertex was at the peak point
                So this means the face is the top face. Only works for the first layer. Other layers require more work (other part of if statement)
                '''
                for face in tempObj.Faces:                                      #Runs through all faces in the newest feature
                    count = 0
                    for vertex in face.Vertexes:                                #Extracts each vertex in the face
                        #print("Z value is {:.4f} and height is {:.4f}".format(vertex.Z,(z_value[-1]+layer_thickness))) #For debugging
                        if vertex.Z >= z_value[-1]+layer_thickness-.0005:       #If the vertex's Z point is equal to the current top location, or very clsoe
                            #print("Current count is {:.2f} out of {:.2f}".format(count,len(face.Vertexes)))
                            count +=1
                    if count == len(face.Vertexes):                             #If all Vertices have the max z value then this is right face
                        foi = face
                        #Part.show(foi)                                         #For debugging
                #print(foi.Edges)                                               #For debugging
                #justHoles = justHoles.cut(foi)
                #Part.show(justHoles)

                '''
                Below section first runs through all the edges from the previously found top face and takes out only the outside edges, ignoring all the
                edges that would be part of the hole section (still on top but not an outside edge). Using this new list it compares all the outside edges
                to the edges of the original object to get the edge nubmers (index numbers) of the original object: without this comparison the original object
                cannot be chamfered. These edges are then added into the list of edges to chamfer.
                '''
                outerEdges = []                                                 #Grabs outside edges, ignores the edges near the hole
                for edge1 in foi.Edges:
                    for idx, edge2 in enumerate(justHoles.Edges):               #Runs through edges from the hole object
                        if round(edge1.firstVertex().Point[2],2) == round(edge2.firstVertex().Point[2],2): #If at same height (only top hole edges)
                            if (edge1.firstVertex().Point[0] == edge2.firstVertex().Point[0] and edge1.firstVertex().Point[1] == edge2.firstVertex().Point[1]) or \
                            (edge1.lastVertex().Point[0] == edge2.lastVertex().Point[0] and edge1.lastVertex().Point[1] == edge2.lastVertex().Point[1]): #If any of the points are not equal
                                #continue
                                #print("Vertices were equal")
                                break
                            #print(idx, len(justHoles.Edges))
                            if idx == len(justHoles.Edges)-1:                   #If edges at same height and all edge comparisons have failed (no matching ones)
                                outerEdges.append(edge1)                        #Then this must be an outside edge
                            #else:
                                #outerEdges.append(edge1)
                                #Part.show(edge2)
                        elif idx == len(justHoles.Edges)-1:                     #If all other comparisons have been made and failed
                            outerEdges.append(edge1)                            #Then this must be an outside edge
                #print(outerEdges)                                              #For debugging

                edgeNums = []; indexing = 0                                     #Used to keep track of the edge numbers needed to chamfer
                for edgeMain in polyFeature.Shape.Edges:                        #Runs through all edges in the original shape (the new feature)
                    indexing += 1; count = 0
                    for edgeFace in outerEdges:                                 #Runs through each edge in the outside edges
                        #print(edgeMain.firstVertex().Point, edgeFace.firstVertex().Point)  #For debugging
                        if edgeMain.firstVertex().Point == edgeFace.firstVertex().Point and edgeMain.lastVertex().Point == edgeFace.lastVertex().Point:
                            edgeNums.append(indexing)                           #If the start and end vertex of the edges are same then add the index to array
                            break
                #print(edgeNums)                                                #For debugging
                #edgeNums = [46,49]#33,34,35]                                   #For debugging
                myEdges = []                                                    #Edge array for chamfer function
                for i in range(0, len(edgeNums)):                               #Runs through all the edges on top face as found from above for loop
                    #For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face *Needs to be the angle*)
                    #Should be edges 4,7,10,12 for basic features (these are always top edges for a rectangular prism)
                    myEdges.append((edgeNums[i], layer_thickness-.0001, layer_thickness*math.tan(angle) ))
                chamfLIL1[-1].Edges = myEdges                                   #Creates list of all chamfer edges
                '''
                Below section takes the chamfered objects and shifts it down .0001, then cuts off that .0001 that isn't chamfered at bottom and creates a new
                feature for it. This alleviates the need to do more complicated searches to take the extra .0001 into account, and clears up errors with top edges
                switching directions because of the additional edges at bottom (caused a flip on which way was the Z direction for chamfer.Edges). Deletes the disconnect
                at the .0001 that would otherwise occur in future depositions as well. Ultimately it also cleans up the code, but adds a .1um error to all feature heights.

                **This can potentially change in the future by extruding the object more than its designated thickness and then just cut off the bottom of the
                feature similar to what is being done here, but it would be trimming excess instead of part of the feature itself.
                '''
                FreeCAD.ActiveDocument.recompute()                              #Recompute is basically reload for FreeCAD, reloads all objects in display
                placement1 = FreeCAD.Placement()                                #Placement vectors are used to move objects inside FreeCAD
                placement1.move(FreeCAD.Vector(0,0,-.0001))		                #This defines the movement based off created vector
                chamfLIL1[-1].Placement = placement1                            #This moves desired object the specificied amount
                newChamf = FreeCAD.ActiveDocument.addObject("Part::Feature", "tempChamf")
                newChamf.Shape = chamfLIL1[-1].Shape.cut(topObj.Shape)          #Cuts the .0001 unchamfered portion on the deposition layer
                #Need to delete the old chamfer here and add the new one
                FreeCAD.ActiveDocument.removeObject(chamfNames[-1])             #Deletes the myChamferX object
                chamfNames.pop()                                                #Deletes the myChamferX name
                chamfLIL1.pop()                                                 #Removes the chamfer object from array
                chamfNames.append("newChamf"+str(len(chamfNames)))              #Creates new chamfer name for the fixed object
                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
                chamfLIL1[-1].Shape = newChamf.Shape
                FreeCAD.ActiveDocument.removeObject("tempChamf")                #Deletes the tempChamf object
                print("After obj chamfer")
        else:                                                                   #Objects layered on top of other objects
            '''
            Below section removes the faces that make up the hole (via) from the object (if there is one), it keeps track of it to fuse it back at the very
            end of the chamfering process. This is important to remove or else the code will try to chamfer the edges of the hole as well causing errors to
            occur in FreeCAD. It is also important so the top edges connecting the hole part and the flat part are not included in the chamfer list.
            The removal occurs in multiple steps, first removing the basic faces and second running through and making sure any divisions beneath the first layer
            are not included in the face array. This second part can be taken out if the deposition occurs properly

            **This has been tested for holes that go through 1 and 2 layers, more layers has not yet been tested, but should work. It is possible to speed this
            section up.
            '''
            botFaceRem = []
            holeFaces = []
            for idx, face in enumerate(bottomFaces):                            #Inspects every face that was considered to be a bottom face
                for obj in layerLIL:                                            #Compares the face to every layer that has been previously created
                    if face.distToShape(obj.Shape)[0] < .1:                     #This comparison allows for multi-layer holes
                        #Part.show(face)                                        #For debugging
                        botFaceRem.append(idx)
                        break
            for rem in sorted(botFaceRem, reverse=True):                        #Loop to remove the hole faces, in reverse to not mess up indexing
                holeFaces.append(bottomFaces[rem])                              #Keeps track of all the faces removed, to later compare to
                bottomFaces.pop(rem)
            #for face in bottomFaces:                                           #For debugging to ensure the first
            #    Part.show(face)
            for face in polygon.Shape.Faces:                                    #Catches additional faces that were not bottom faces and adds them to the array of hole faces
                for obj in layerLIL:                                            #Again runs through every layer that has been created
                    if face.distToShape(obj.Shape)[0] < .01:
                        #for faces in holeFaces:                                #For debugging
                        #    if face != faces
                        holeFaces.append(face)
            '''
            The below for loop can likely be taken out, depening on if the deposition is smooth or if extra edges occur between
            multi-layer holes
            '''
            botFaceRem = []                                                     #Used to keep track of additional faces that can sometimes occur between multi-layer holes
            for idx, face in enumerate(bottomFaces):
                faceSurface = face.Surface
                pt=Base.Vector(0,1,0)
                param = faceSurface.parameter(pt)
                #print(param)
                norm = face.normalAt(param[0],param[1])
                #print(norm)
                #if abs(norm[2]) != 0:# != 1 and abs(norm[1]) != 1: #If the face is oriented to one of the sides (something we don't want)
                #    bottomFaces.append(face)
                for faceHole in holeFaces:
                    if face.distToShape(faceHole)[0] < .01:
                        faceSurface2 = faceHole.Surface
                        pt2=Base.Vector(0,1,0)
                        param2 = faceSurface2.parameter(pt2)
                        norm2 = faceHole.normalAt(param2[0],param2[1])
                        #print(norm, norm2)
                        normArr = np.array(norm)#np.absolute(np.array(norm))    #Using absolute values can sometimes pick up other nearby angled faces
                        norm2Arr = np.array(norm2)#np.absolute(np.array(norm2)) #Usage of the absolute values is not recommeneded
                        #print(np.allclose(normArr,norm2Arr,1e-5))              #For debugging, returns True or False depending if the vertex (X,Y,Z) components are all within 1e-5
                        if np.allclose(normArr,norm2Arr,1e-5) == True:#norm == norm2:#(norm > norm2-.001) and (norm < norm2+.001): #If they share the same normal and are touching
                            botFaceRem.append(idx)
            #for face in holeFaces:                                             #For debugging
            #    Part.show(face)
            for rem in sorted(botFaceRem, reverse=True):
                holeFaces.append(bottomFaces[rem]) #Does not matter that they are reversed
                bottomFaces.pop(rem)
            #for face in holeFaces:                                             #For debugging
            #    Part.show(face)
            '''
            The below section takes all the bottom faces of the passed polygon and extrudes them by the desired amount (creating FreeCAD objects for each, required
            for chamfering). It then goes through and trims off the excess edges of all the objects that forms from the angled objects, creating a new list
            of cleaned objects. This only considers faces that are not part of the hole, as all hole faces should have been removed.
            '''
            separateObjNames = []                                               #Used to declare names for each object feature
            separateObj = []                                                    #Used to hold all the separated objects
            for counter,face in enumerate(bottomFaces):                         #Runs through all the bottom faces to create objects from them
                tempObj = face.extrude(Base.Vector(0,0,layer_thickness+.00015)) #Initial extrusion, extra .00015 to account for a slight hole height difference
                separateObjNames.append("tempObj" + str(counter))               #Creates a name for the objects
                separateObj.append(FreeCAD.ActiveDocument.addObject("Part::Feature", separateObjNames[-1])) #Creates FreeCAD features for each of the objects
                separateObj[-1].Shape = tempObj                                 #Initializes the feature shape to that of the initial extrusion
                FreeCADGui.ActiveDocument.getObject(separateObjNames[-1]).Visibility = False #Removes the visibility, allowing program to run faster - these get deleted later on
            cleanedSeparateObj = []                                             #Used to store all the separate objects after they have been cut
            for outer, extrusion in enumerate(separateObj):                     #For all the shapes subtract out every other shape
                noObj = True                                                    #Used to tell if there is an object on the first outershell section
                for inner,otherExtrusions in enumerate(separateObj):            #For all the shapes, fuse them all together except for the one from outer loop
                    if outer==inner:                                            #If looking at the same object then skip the comparison
                        continue
                    elif noObj:                                                 #First loop through, set the tempObj equal to the otherExtrusions
                        noObj = False                                           #If there has been no object added yet
                        tempObj2 = otherExtrusions.Shape
                    else:                                                       #Fuses all aditional objects
                        tempObj2 = tempObj2.fuse(otherExtrusions.Shape)
                #Part.show(tempObj2)                                            #For debugging
                cleanedSeparateObj.append(extrusion.Shape.cut(tempObj2).removeSplitter()) #Appends the newly cut objects to the array (as Shapes) and removes any excess edges
                #Part.show(cleanedSeparateObj[-1])                              #Used to debug that the proper shape was created
            holeSections = polygon.Shape.cut(cleanedSeparateObj[0])             #This object will hold the shape of just the hole
            for shape in cleanedSeparateObj[1:]:                                #Removes all the new objects (pieces of the polygon) until just the hole is left
                holeSections = holeSections.cut(shape)
            #Part.show(holeSections)                                            #Used for debugging to ensure that the hole is the only thing left after removal
            '''
            Now all the objects are created, so need to find all the correct edges and chamfer them.
            Below section is designed to to get rid of the bottom and side faces of our object, so that only the top edges are considered.
            It starts by verifying the normal has a Z component (deletes side faces), it then checks to ensure that all edges are not touching the
            layer the feature was created on top off. Lastly it checks to ensure that the raised sections that still touch the deposit layer
            is deleted.

            **This could likely be increased in speed by checking the distance to the deposit layer and veryfying it is greater than zero.
            '''
            finalPolygonArray = []                                              #Will hold all the chamfered polygons
            faceToInspect = []
            for face in polygon.Shape.Faces:                                    #This loop gets rid of all the side faces
                faceSurface = face.Surface
                #Part.show(polygon.Shape.Faces[0])
                pt=Base.Vector(0,1,0)
                param = faceSurface.parameter(pt)
                #print(param)
                norm = face.normalAt(param[0],param[1])
                #print(norm)
                if abs(norm[2]) > 0 :                                           #If the face has a z component
                    for edge in face.Edges:                                     #This loop verifies all edges on the top, except for objects layered on top of others (deleted after)
                        if edge.firstVertex().Point[2] >= layer_thickness+depositionThickness[-1] and edge.lastVertex().Point[2] >= layer_thickness+depositionThickness[-1]:
                            faceToInspect.append(face)                          #Keeps track of all the faces that edges are needed from
                            break                                               #If face is added, break out of the for loop so it doesn't get added again
            breakLoop = 0                                                       #Break counter for following loops
            faceRemovalArray = []                                               #Keeps track of the indices that need to be removed from the faceToInspect array
            #Can maybe make below loops faster by just checking the distance from the faces to the dep layer, versus all this mayhem
            dep_obj2 = FreeCAD.ActiveDocument.getObject(topObj.Label)#holeNames[-1])          #Copies the last hole layer for face comparison
            for i in range(0,len(faceToInspect)):               #For all newly added faces, compare vertices to vertices of the last hole layer, if they match then remove the face
                #This will get rid of the faces that are at the required height, but touching the hole layer layer, i.e. on top of features
                for edge in faceToInspect[i].Edges:
                    for eoi in dep_obj2.Shape.Edges:                            #Grabs all vertices from previous hole layer layer
                        if edge.firstVertex().Point[2] == eoi.firstVertex().Point[2] or edge.lastVertex().Point[2] == eoi.lastVertex().Point[2]:
                            if edge.firstVertex().Point[0] == eoi.firstVertex().Point[0] or edge.firstVertex().Point[1] == eoi.firstVertex().Point[1]:
                                #print(edge.distToShape(dep_obj.Shape))         #For debugging
                                if edge.distToShape(dep_obj2.Shape)[0] == 0:
                                    faceRemovalArray.append(i)                  #Tracks the face that matches vertices with the deposition layer
                                    breakLoop += 1                              #If this increments need to stop comparing edges and break the second loop too
                                    break                                       #breaks out of third for loop
                    if breakLoop == 1:                                          #If previous loop was broken out of
                        breakLoop = 0
                        break                                                   #Breaks out of second for loop
            #print(faceRemovalArray)
            for rem in sorted(faceRemovalArray, reverse=True):                  #Deletes the indicies in reverse to not mess up the index order
                del faceToInspect[rem]                                          #Removes the edges on top of the features
            '''
            Below section takes the top faces and finds all the edges that need to be chamfered from it. First it creates a shell, which is one object
            of all the faces, then it finds the outside boundary wires of that shell. This technically creates a single object from all the previously separated
            objects, it is again seperated in the following for loop.
            '''
            new_obj=FreeCAD.ActiveDocument.addObject("Part::Feature","NewObj")  #new object used as a shell to search for all the edges, variable resuable
            new_obj = Part.makeShell(faceToInspect)                             #use Part.Shell not Part.Compound as Part.Compound does only generic grouping
            boundary = []                                                       #Finds a boundary list for all the outside edges
            for face in new_obj.Faces:
                for edge in face.OuterWire.Edges:
                    ancestors = new_obj.ancestorsOfType(edge, Part.Face)
                    if len(ancestors) == 1:
                        boundary.append(edge)
            #boundaryWire = boundary[0].multiFuse(boundary[1:])                 #Used for debugging, includes the edges at the face intersections
            #Part.show(boundaryWire)                                            #For debugging
            edgeList = boundary#                                                #Edge list to how all the edges needed for the chamfer, keeping name for consistency
            '''#The following 3 lines are used for debugging, to ensure the proper boundary edges were found
            tempWire = Part.makePolygon(edgeList)
            tempFace = Part.Face(tempWire)
            Part.show(tempFace)'''

            '''
            Below for loop runs through every face (all top faces) of the new objects and finds the desired edges from the original object needed to chamfer.
            For some reason there is a blank object at end of the cleanedSeparateObj list, or at least it shows up while trying to chamfer.

            ** Could part of this be taken out to increase running speed?
            '''
            for counter, polyShape in enumerate(cleanedSeparateObj):
                #Part.show(polyShape.Faces[0])
                #Part.show(polyShape) #For debugging
                print("At start of object separation")
                for face in polyShape.Faces:                                    #Loop to find all the bottom faces
                    if face.distToShape(topObj.Shape)[0] > .1:
                        faceToInspect2 = face
                        #Part.show(face)
                        break
                #print("Number of faces in faceToInspect" + str(faceToInspect2)) #For debugging, should only be 1 edge
                '''
                Below section takes the boundary wires of all the new objects and compares them to the edges of the oringinal feature, the edge number (index) of
                the original feature is then recorded. This is important because edge numbers are generated uniquely and so the new objects do not share the edge numbers
                of the original feature.

                edgeList contains the edges of the main shape, faceToInspect2 is the top face of the new object, and edgeList 2 will hold the edges needed for the final
                comparison.

                **After fixing the issue with FreeCAD not being able to chamfer the entire height of an object, part of the following might be able to be removed.
                '''
                edgeList2 = []                                                  #Edge list of all the edges needed for the chamfer
                for counterT, edgeToAdd in enumerate(faceToInspect2.Edges):     #Checks every edge in boundary array to ensure they are not between two faces (only true boundary edges)
                    for counter3,edgeExists in enumerate(edgeList):             #Runs through every edge currently in edgeList, comparing to the newly added edge
                        toAddX1 = round(edgeToAdd.firstVertex().Point[0],2); toAddY1 = round(edgeToAdd.firstVertex().Point[1],2); toAddZ1 = round(edgeToAdd.firstVertex().Point[2],2)
                        existsX1 = round(edgeExists.firstVertex().Point[0],2); existsY1 = round(edgeExists.firstVertex().Point[1],2); existsZ1 = round(edgeExists.firstVertex().Point[2],2)
                        toAddX2 = round(edgeToAdd.lastVertex().Point[0],2); toAddY2 = round(edgeToAdd.lastVertex().Point[1],2); toAddZ2 = round(edgeToAdd.lastVertex().Point[2],2)
                        existsX2 = round(edgeExists.lastVertex().Point[0],2); existsY2 = round(edgeExists.lastVertex().Point[1],2); existsZ2 = round(edgeExists.lastVertex().Point[2],2)
                        '''For debugging
                        print("ToAdd1")
                        print(toAddX1,toAddY1,toAddZ1)
                        print(existsX1,existsY1,existsZ1)
                        print("ToAdd2")
                        print(toAddX2,toAddY2,toAddZ2)
                        print(existsX2,existsY2,existsZ2)'''

                        '''
                        Because new objects were created to separate out the edges for chamfering some of the edges might not be going in the same direction
                        For example, one edge that might be shared (the same edge) could actually have firstVertex and lastVertex flipped
                        This is normally not the case after fixing the subtraction issue with not chamfering the entire object height, but if this error does occur
                        it can be fixed by using the __sortEdges__ (function call might be mispelled) function for FreeCAD .19 and later

                        **Might be able to remove the below if statement due to fixing the .0001 difference issue
                        '''
                        if (toAddX1 == existsX1 or toAddX1 == existsX2) and (toAddY1 == existsY1 or toAddY1 == existsY2) and \
                        (toAddZ1 == existsZ1 or toAddZ1 == existsZ2) and (toAddX2 == existsX2 or toAddX2 == existsX1) and \
                        (toAddY2 == existsY2 or toAddY2 == existsY1) and (toAddZ2 == existsZ2 or toAddZ2 == existsZ1): #This accounts for the .0001 difference when comparing them
                        #if edgeToAdd.distToShape(edgeExists):                  #Can try using this instead
                            ''' For debugging
                            print("ToAdd1")
                            print(toAddX1,toAddY1,toAddZ1)
                            print(existsX1,existsY1,existsZ1)
                            print("ToAdd2")
                            print(toAddX2,toAddY2,toAddZ2)
                            print(existsX2,existsY2,existsZ2)'''
                            #print("Edge Equal")                                #For debugging
                            edgeList2.append(edgeToAdd)
                            break                                               #This skips the edge, meaning it is not a unique edge
                #newWire2 = edgeList2[0].multiFuse(edgeList2[1:])               #Creates a new wire out of all the edges, for debugging
                #Part.show(newWire2)                                            #Used for debugging, show all the edges on the top boundary
                '''
                Below for loop accounts for the inside edges connecting the hole section to the new objects. It runs through and if an edge is shared then it removes
                the edge.

                **Could be made fast by considering that only a few objects can interact with the hole edges, could maybe keep track of those and stop running this if
                they have been encountered
                '''
                remHoleEdge = []                                                #New array to hold the edge values alongside the hole
                for idx, edge1 in enumerate(edgeList2):                         #Runs through every edge being considered for chamfering
                    outsideBreak = False
                    for face in holeFaces:                                      #For every face inside the list previously found
                        for edge2 in face.Edges:                                #Loops every edge to find if any edges are shared
                            if (edge1.firstVertex().Point[0] == edge2.firstVertex().Point[0]) and (edge1.firstVertex().Point[1] == edge2.firstVertex().Point[1]) \
                                    and (edge1.lastVertex().Point[0] == edge2.lastVertex().Point[0]) and (edge1.lastVertex().Point[1] == edge2.lastVertex().Point[1]):
                                remHoleEdge.append(idx)
                                outsideBreak = True                             #If the edge has been added then need to stop the inspection to the inside face
                                break                                           #Break to keep an edge from being added multiple times
                        if outsideBreak == True:                                #Breaks out of the 2nd for loop to move on to the next edge comparison
                            break
                for rem in sorted(remHoleEdge, reverse=True):                   #Deletes the indicies in reverse to not mess up the index order
                    del edgeList2[rem]
                '''
                Below section takes the newly found edges and compares them to the original object. It takes the index of the original object's edges
                that are equal to the edges in the edgeList2 and uses those to create the chamfer edges. It then chamfers the objects to the specified angle
                and cleans up. Chamfers for angled objects are more complex and the actual height of that object will depend on the angle and thickness
                of the object it is layered on top of. To get around this the height of the angle objects is found and then inserted into the chamfer height.
                '''
                print("After edge selection")
                polyFeature = FreeCAD.ActiveDocument.addObject("Part::Feature", "SillyName"+str(counter))                    #Must create this to set chamfer base equal to
                polyFeature.Shape = polyShape
                chamfNames.append("myChamf"+str(counter+numOfChamfNames2))                                                   #Creates new chamfer name, 0 is f is layerDevelop
                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Chamfer", chamfNames[counter+numOfChamfNames2]))    #Creates new chamfer inside FreeCAD, 0 should be number of features up to here, used as f above
                chamfLIL1[counter+numOfChamf2].Base = polyFeature               #Adds the new feature as the base to chamfer
                edgeNums = []
                indexing = 0
                #tempArr4 = [3,33]                                              #used for debugging edge selection
                for edgeMain in polyShape.Edges:                                #Runs through all edges in the original shape
                    indexing += 1; count = 0
                    for edgeFace in edgeList2:                                  #Runs through each edge in the desired face (top face)
                        if edgeMain.firstVertex().Point == edgeFace.firstVertex().Point and edgeMain.lastVertex().Point == edgeFace.lastVertex().Point:
                            edgeNums.append(indexing)                           #If the start and end vertex of the edges are same then add the index to array
                print(edgeNums)                                                 #For debugging
                print("After edge indexing ")
                #edgeNums = list(set(edgeNums))                                 #For some reason, one edge can get added multiple times so this gives only unique numbers
                myEdges = []                                                    #Edge array for chamfer function
                #tempedgeNums = [4,10] #Temporary list since the whole edgeNums list doesn't work
                #print(edgeList2)
                '''
                Below section adds the chamfer edges to the chamfer list along with the amount to chamfer. Due to quirks in FreeCAD the amount needed to chamfer the entire
                height of the object will vary depending on if it is flat or angled. The first section below finds the tangent to test if the object is flat or angled (on top of
                another feature). The flat objects are straightforward with the amount needed to chamfer simply being the thickness of the object. The angled features vary depending
                on the chamfer and and the angle of the feature it is laid on top of. This problem is solved by finding the height of the angled object in relation to the deposition
                layer below it and then taking an adjusted amount off from there: the .00002 allows objects angled from 5 to 65 to be chamfered properly. Larger angles can have
                more unchamfered (i.e. .0001), but smaller angles require less left behind which is then subtracted out when making "newChamf" Features.

                **Might need to sort edges before chamfering depending on how the cut feature creates the new objects, but generally this should not be the case (debug this later).
                '''
                flat = False
                for face in polyShape.Faces:                                    #Searches all the faces in the passed polygon looking for just bottom faces
                    if face.distToShape(dep_obj2.Shape)[0] < .01:               #If the face intersects with the deposition layer then it is at the bottom
                        faceSurface = face.Surface
                        pt=Base.Vector(0,1,0)
                        param = faceSurface.parameter(pt)
                        #print(param)
                        norm = face.normalAt(param[0],param[1])
                        #print(norm)
                        if abs(norm[2]) == 1:                                   #If the face is oriented only in the Z direction
                            flat = True                                         #This means the object is not layered on another feature (not angled)
                if flat == True:                                                #For objects that are not layered on top of another object (not angled)
                    for i in edgeNums:                                          #Runs through all the edges on top face as found from above for loop
                        #For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face (set at the desired angle))
                        myEdges.append((i,layer_thickness+.00005,layer_thickness*math.tan(angle) )) #The .00005 is added for a varience in the hole layer height
                        #print(i)                                               #Prints edge index, for debugging
                else:                                                           #If the object is angled (layered on top of another feature)
                    print(dep_obj2.Label)
                    angHeight = edgeList2[0].firstVertex().distToShape(dep_obj2.Shape)[0]#topObj.Shape)[0]#dep_obj2.Shape)[0] #Gets distance from the top edge to the deposition layer
                    print(angHeight)
                    for i in edgeNums:                                          #Runs through all the edges on top face as found from above for loop
                        #For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face (set at the desired angle))
                        '''
                        For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face (set at the desired angle))
                        For some reason the angled features are not as thick as the regular ones. For a layer_thickness of 1, the angled features
                        only have a thickness of .85099, so about 85.099% as thick.
                        For angled objects, the amount needed to chamfer the Z portion will vary depending on the angle of the features below it
                        and its own angle and sometimes on the thickness
                        '''
                        myEdges.append((i,(angHeight)-.00002,layer_thickness*math.tan(angle)))
                        print(i)                                               #Prints edge index, for debugging
                chamfLIL1[-1].Edges = myEdges                                   #Creates list of all chamfer edges
                FreeCAD.ActiveDocument.recompute()                              #Recompute is basically reload for FreeCAD, reloads all objects in display
                #chamfLIL1[-1].Shape = chamfLIL1[-1].Shape#.fuse(holeSections)
                finalPolygonArray.append(chamfLIL1[-1].Shape)                   #Holds all the chamfered shapes to create a single layer out of
                FreeCADGui.ActiveDocument.getObject(polyFeature.Label).Visibility = False
                '''
                Below section takes the chamfered objects and shifts it down .0001, then cuts off that .0001 that isn't chamfered at bottom and creates a new
                feature for it. Experimenting with this to see if it will alleviate the need for the complicated searches above, and clear up the incorrect directions
                of edges that occur when there is a disconnect from the .0001 distance. So it should fix the disconnect of edges and clean up the code. It does these nicely
                but causes an offset in each layer that stacks up over time. Eventually if there are enough layers this can cause a small breakdown in the code. Generally
                the deposition layer should take care of some of this, but ultimately this will need to get fixed.

                **One method that could fix this is increasing the initial extrusion and then chamfering just the layer thickness amount before cutting off that extra extrusion
                value
                '''
                placement1 = FreeCAD.Placement()                                #Placement vectors are used to move objects inside FreeCAD
                placement1.move(FreeCAD.Vector(0,0,-.0001))		                #This defines the movement based off created vector
                chamfLIL1[-1].Placement = placement1                            #This moves desired object the specificied amount
                newChamf = FreeCAD.ActiveDocument.addObject("Part::Feature", "tempChamf")
                newChamf.Shape = chamfLIL1[-1].Shape.cut(topObj.Shape)          #Cuts the .0001 unchamfered portion on the deposition layer
                #Need to delete the old chamfer here and add the new one
                FreeCAD.ActiveDocument.removeObject(chamfNames[-1])             #Deletes the myChamferX object
                chamfNames.pop()                                                #Deletes the myChamferX name
                chamfLIL1.pop()                                                 #Removes the chamfer object from array
                chamfNames.append("newChamf"+str(numOfChamfNames2+counter))     #Creates new chamfer name for the fixed object
                chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
                chamfLIL1[-1].Shape = newChamf.Shape
                FreeCAD.ActiveDocument.removeObject("tempChamf")                #Deletes the tempChamf object
                print("After obj chamfer")

        if len(holeSections.Faces) != 0:                                    #If there was a hole inside this feature, need to also add it back to the final object
            #Part.show(holeSections)
            '''
            This section simple creates a new object for the hole section under the same name as the regular chamfer objects.
            This is required for the hole section to be properly fused back together with the final layer object.
            '''
            chamfNames.append("newChamf"+str(len(chamfNames)))     #Creates new chamfer name for the fixed object
            chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
            holeSections.Placement.move(FreeCAD.Vector(0,0,-.000025))
            chamfLIL1[-1].Shape = holeSections

    else:                                                                       #If there is 0 chamfer angle (no chamfer being performed)
        '''
        This section simple creates a new object for the polygon under the same name as the regular chamfer objects.
        This is required for the polygon to be properly fused back together with the final layer object.
        '''
        chamfNames.append("newChamf"+str(len(chamfNames)))                      #Creates new chamfer name for the fixed object
        chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
        chamfLIL1[-1].Shape = polygon.Shape

'''Some comment updates need to be made here when closer to finalizing the function'''
def holeCreation(all_polygons_dict, layerNum, layer_thickness, angle, holeLayerName, bias = 0):
    '''
    holeCreation function takes an already created layer and makes holes (vias) in that layer. The holes are only created one layer at a time so multi-layered
    holes will require a second function call, generally the higher layer will also require a bias to properly match the lower layer's hole. It begins by
    taking each of the objects in the hole layer and creating FreeCAD features, it then places them overlapping the the layer with holes being cut in it, tapers
    if needed along the bottom edge of the object (as opposed to the top edges), and then subtracts the holes from the layer to get the final updated layer.

    Function updates the lastDeposited, layerThickness, and depositLIL arrays.

    Inputs: the polygon dictionary, layer containing the hole geometries, the desired deposition thickness, the angle to taper at, the layer
    in which the holes will be made, and any associated bias. Bias values are reversed here from regular features, such that a negative bias will
    make the hole larger.

    Returns: Nothing, all edits are done in place, but can return the final shape of the edited layer with holes.
    '''
    layerThickness.append(layer_thickness)
    #print(holeLayerName.Label)                                                 #For debugging
    holeLayer = holeLayerName.Shape.copy()                                      #Creates a copy of the layer that needs the holes
    #Part.show(holeLayerName.Shape)                                             #For debugging
    #poly =sp.get_xy_points(all_polygons_dict[layerNum][0])
    '''for point in holeLayerName.Shape.Vertexes:
        if round(poly[0][0],4) == round(point.Point[0],4) and round(poly[0][1],4) == round(point.Point[1],4):
            zVal = sp.topXY(poly[0][0],poly[0][1],holeLayerName.Label) - layer_thickness
            break'''
    #zVal = sp.topXY(holeLayerName.Shape.Vertexes[0].Point[0], holeLayerName.Shape.Vertexes[0].Point[1], holeLayerName.Label) - layer_thickness
    for f in range(0,len(all_polygons_dict[layerNum])): #Goes through all polygons in given key (layerNum)
        polyLayer = sp.get_xy_points(all_polygons_dict[layerNum][f])   #Converts all to mm
        #z_value = 3.0
        '''zVal needs to find the topXY point for the given obj to create holes in and then move down by layer_thickness, this should be for every Z maybe?'''
        #zVal = holeLayer.Shape.Vertexes[0].Point[2]#sp.topXY(polyLayer[0][0],polyLayer[0][1],depositNames[-1]) #Finds the highest point at given X,Y value and uses it as height
        #zVal = sp.topXY(polyLayer[0][0], polyLayer[0][1], holeLayerName.Label) - layer_thickness
        if "Planar" in holeLayerName.Label:
            for idx, name in enumerate(lastDeposited):      #Finds the object beneath the one being cut through
                print(holeLayerName.Label, name.Label)
                if holeLayerName.Label in name.Label:
                    previousLayer = idx - 1
                    break
            #maxH =
            #print()
            #zVal = sp.topXY(polyLayer[0][0], polyLayer[0][1], holeLayerName.Label) - sp.topXY(polyLayer[0][0], polyLayer[0][1], lastDeposited[previousLayer].Label)
            #zVal = sp.topXY(polyLayer[0][0], polyLayer[0][1], lastDeposited[previousLayer].Label)
            #print(lastDeposited[previousLayer].Label, zVal)
            print(sp.topXY(polyLayer[0][0], polyLayer[0][1], holeLayerName.Label), sp.topXY(polyLayer[0][0], polyLayer[0][1], lastDeposited[previousLayer].Label))
            layer_thickness = 3#sp.topXY(polyLayer[0][0], polyLayer[0][1], holeLayerName.Label) - sp.topXY(polyLayer[0][0], polyLayer[0][1], lastDeposited[previousLayer].Label)
        #else:
        zVal = sp.topXY(polyLayer[0][0], polyLayer[0][1], holeLayerName.Label) - layer_thickness
        #for obj in FreeCAD.ActiveDocuments.Objects:
        #zVal finds the total object thickness by taking the height on top of the object being cut minus the height of the object beneath it
        #zVal = sp.topXY(polyLayer[0][0], polyLayer[0][1], holeLayerName.Label) - sp.topXY(polyLayer[0][0], polyLayer[0][1], lastDeposited[previousLayer].Label)
        '''Below section adds the bias to objects. It takes every vertex and compares it to the next one, one of those vertices gets an addition to x or y
        and the other vertex gets a subtraction to x or y. This bias currently works as an addition (makes the feature larger) to imitate etching.'''
        if bias != 0:
            xChange = False; yChange = False                                    #Booleans used to keep one vertex from changing multiple times along same axis
            verts = len(polyLayer)
            xChanges = [bias]*verts; yChanges = [bias]*verts                    #Store changes so they are only updated at the end
            for idx, point in enumerate(polyLayer):
                if idx == verts-1:                                              #If looking at last vertex of the shape, the next vertex is the first vertex
                    next = 0
                else:
                    next = idx+1
                if point[0] == polyLayer[next][0]:                              #Share same x point, update the y-axis values
                    if yChange == False:
                        if point[1] > polyLayer[next][1]:                       #Compares actual value, abs value would cause inverse errors if crossing axis
                            yChanges[idx] = -bias
                            yChanges[next] = bias
                            yChange = True
                        else:
                            yChanges[idx] = bias
                            yChanges[next] = -bias
                            yChange = True
                    else:
                        yChange = False
                else:
                    yChange = False
                if point[1] == polyLayer[next][1]:                              #Share same y point, update the x-axis values
                    if xChange == False:
                        if point[0] > polyLayer[next][0]:                       #Compares actual value, abs value would cause inverse errors if crossing axis
                            xChanges[idx] = -bias
                            xChanges[next] = bias
                            xChange = True
                        else:
                            xChanges[idx] = bias
                            xChanges[next] = -bias
                            xChange = True
                    else:

                        xChange = False
                else:
                    xChange = False
            #print(len(polyLayer),len(xChanges),len(yChanges))                  #For debugging
            #print(xChanges)                                                    #For debugging
            #print(yChanges)                                                    #For debugging
            for id, point2 in enumerate(polyLayer):
                point2[0] = point2[0] + xChanges[id]
                point2[1] = point2[1] + yChanges[id]
                point2.append(zVal)
            polyLayer[0][0] = polyLayer[-1][0]                                  #Sets the last and first point equal to ensure updates were done properly
            polyLayer[0][1] = polyLayer[-1][1]                                  #This is required since only the last point (technically 4) gets updated (not 0)
        else:
            for point in polyLayer:
                point.append(zVal)
        print("Before layerDevelop Object")                                     #For debugging
        #print(sp.topXY(polyLayer[0][0],polyLayer[0][1],depositNames[-1]), z_value[-1]) #For debugging
        pts=[]
        for i in range(0,len(polyLayer)):                                       #Used to create an array of the "Vector points" required in FreeCAD
            pts.append(FreeCAD.Vector(polyLayer[i][0],polyLayer[i][1],polyLayer[i][2])) #FreeCAD.Vector(x,y,z)
        wire=Part.makePolygon(pts)                                              #Connects all points given above, makes a wire polygon (just a line)
        face=Part.Face(wire)                                                    #Creates a face from the wire above
        #Part.show(face)                                                        #For debugging
        extrusionLIL1.append(face.extrude(Base.Vector(0,0,layer_thickness+.1))) #Creates an extrusion from the new face
        #Part.show(extrusionLIL1[-1])                                           #Used to show the extrusion object - only used for debugging
        print("Before Chamfer")                                                 #For debugging
        holeNames.append("myHole"+str(len(holeNames)))                          #Creates new feature name
        holeLIL.append(FreeCAD.ActiveDocument.addObject("Part::Feature", holeNames[-1])) #Creates new feature inside FreeCAD
        holeLIL[-1].Shape = extrusionLIL1[-1]                                            #Adds previous extrusion and the feature shape
        botEdges = []
        for edge in holeLIL[-1].Shape.Edges:                                    #Gets all the bottom edges needed to chamfer
            if edge.distToShape(FreeCAD.ActiveDocument.getObject("Substrate").Shape)[0] == zVal: #If the distance is equal to its original height (no extruded edges)
                botEdges.append(edge)
        #print(botEdges)                                                        #For debugging

        chamfNames.append("myChamf"+str(len(chamfNames)))                       #Creates new chamfer name
        chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Chamfer", chamfNames[-1]))    #Creates new chamfer inside FreeCAD
        chamfLIL1[-1].Base = FreeCAD.ActiveDocument.getObject(holeNames[-1])    #Adds the new feature as the base to chamfer
        '''
        Below runs through all the previously found bottom edges and compares them to the original object to get the edge number from the
        original object. This is required for FreeCAD as edge numbers are unique and the edges from the original object must be pointed to
        for the chamfer or else the original object will not get chamfered properly. It then determines if there are multiple holes, and
        if there are then it will fuse them all together to make the subtraction out from the layer easier.
        '''
        edgeNums = []
        indexing = 0
        for edgeMain in holeLIL[-1].Shape.Edges:                                #Runs through all edges in the original shape (the new feature)
            indexing += 1
            for edgeFace in face.Edges:                                         #Runs through each edge in the desired face (top face)
                #if edgeMain.firstVertex().Point == edgeFace.firstVertex().Point and edgeMain.lastVertex().Point == edgeFace.lastVertex().Point:
                if np.allclose(edgeMain.firstVertex().Point, edgeFace.firstVertex().Point, 1e-4) and np.allclose(edgeMain.lastVertex().Point, edgeFace.lastVertex().Point, 1e-4):
                    edgeNums.append(indexing)                                   #If the start and end vertex of the edges are close then add the index to array
        #print(edgeNums)                                                        #For debugging
        myEdges = []                                                            #Edge array for chamfer function
        for i in edgeNums:                                                      #Runs through all the edges on top face as found from above for loop
            #For below line(edge number, extrusion in -Z direction (must be slightly less than max), extrusion into top face *Needs to be the angle*)
            myEdges.append((i,layer_thickness,layer_thickness*math.tan(angle))) #The object was extruded an additional .0001, so no subtraction necessary here
        chamfLIL1[-1].Edges = myEdges                                           #Creates list of all chamfer edges
        FreeCAD.ActiveDocument.recompute()                                      #Recompute is basically reload for FreeCAD, reloads all objects in display
        if f == 0:                                                              #If this is the first run then this is the first hole
            print("First hole found")
            holeFuse = chamfLIL1[-1].Shape
            #Part.show(holeFuse)                                                #For debugging
            FreeCAD.ActiveDocument.removeObject(chamfNames[-1])                 #Remove the chamfered object (cleaning up)
        elif f >0:                                                              #If multiple holes have been found
            print("Multiple holes founds")
            holeFuse = holeFuse.fuse(chamfLIL1[-1].Shape)                       #Fuse the new hole to any previous holes for later use
            FreeCAD.ActiveDocument.removeObject(chamfNames[-1])                 #Remove the chamfered object (cleaning up)
        else:
            print("No holes present")                                           #If for some reason no objects were in the passed layer
        FreeCADGui.ActiveDocument.getObject(holeNames[-1]).Visibility = False   #Changes the visibility of the fused layer to false, saves graphical computation
        print("After Chamfer")
    '''
    Below section cuts the holes out of the desired layer and then cleans up all the additional objects and holes made before finalizing a hole
    layer as a copy of the edited layer (now with holes). The clean up deletes all the objects created in this function except for the final
    layer with holes, it also deletes the additions to the hole arrays (see global arrays) except for the addition of the final layer with holes.
    '''
    '''holeLayer.Placement.move(FreeCAD.Vector(0,0,.0005))#holeFuse.Placement.move(FreeCAD.Vector(0,0,.0005))'''
    '''for obj in FreeCAD.ActiveDocument.Objects:
        if "myChamf" in obj.Label:
            wholeLayer = wholeLayer.cut(obj.Shape)'''
    #wholeLayer = wholeLayer.cut(chamfLIL1[-rev].Shape)
    wholeLayer = holeLayer.cut(holeFuse)#layerLIL[-1].Shape)#holeFuse)#wholeLayer.cut(chamfLIL1[-1])#holeFuse)
    #Part.show(wholeLayer)
    '''wholeLayer.Placement.move(FreeCAD.Vector(0,0,-.001))#holeFuse.Placement.move(FreeCAD.Vector(0,0,-.001))
    wholeLayer = wholeLayer.cut(holeFuse)
    wholeLayer.Placement.move(FreeCAD.Vector(0,0,.0005))'''
    #Part.show(wholeLayer)
    FreeCADGui.ActiveDocument.getObject(holeLayerName.Label).Visibility = False #Turns off visibility of the layer expecting to get holes cut in it
    #depositLIL.pop()
    #depositNames.pop()
    labels = [obj.Label for obj in FreeCAD.ActiveDocument.Objects]              #Grabs all labels from the current Document
    for label in labels:
        if "myHole" in label:                                                   #If the object is a hole object, delete it
            FreeCAD.ActiveDocument.removeObject(label)
    for i in all_polygons_dict[layerNum]:                                       #Deletes single hole objects that are no longer needed from the arrays
        holeNames.pop()
        holeLIL.pop()
    holeNames.append("myLayerHole"+str(len(holeNames)))                         #Creates new feature name
    holeLIL.append(FreeCAD.ActiveDocument.addObject("Part::Feature", holeNames[-1])) #Creates new feature inside FreeCAD
    holeLIL[-1].Shape = wholeLayer                                              #Sets the new FreeCAd feature shape to the finalized layer
    '''insertInd = 0
    for idx, deps in enumerate(lastDeposited):
        if holeLayerName.Label == deps.Label:
            insertInd = idx
            break'''
    #lastDeposited[insertInd] = holeLIL[-1]
    FreeCAD.ActiveDocument.getObject(holeLayerName.Label).Shape = wholeLayer    #Changes the old layer shape (without holes) into the object with holes
    #lastDeposited.append(holeLIL[-1])
    #layerLIL.append(holeLIL[-1])


#Curved objects are not currently working with the holeDevelop function
#The holeDevelop function takes roughy 65+% of the processing time of the program, including time for taperOverHoles
#The run time of the below function MUST be improved
'''
The below function will not work if account for the .0001 subtraction being made in the layerDevelop function. Meaning if the extrusion
in layerDevelop gets the additional .0001 that is subtracted at the end, then this function fails to work. The reason is due to
an issue in the taperOverHoles (as found so far), but has not been narrowed completely. It is likely an issue with either height or value comparisons.
'''
def holeDevelop(all_polygons_dict, layerNum, layer_thickness, angle, outlineLayer, bias = 0):
    '''The holeDevelop function creates all objects layered on top of holes. It can also create flat object on the same layer, and calls its own taper function.

    Function updates extrusionLIL1, featureLIL1, featureNames, layerNames, layerLIL, layerThickness, z_value, and lastDeposited arrays

    Must be passed the polygon dictionary, the layer number (from XS script), the layer thickness, the taper/chamfer angle (0 if no taper),outlineLayer,
    and a bias value if applicable.

    Returns nothing currently, but can return the final layer object (fused from all the features). '''
    '''Here's the idea. Take the desired objects and extrude them from zero all the way to the highest point + the desired thickness. Then take a temperoary deposition
    which will contain the holes and cut out the bottom and top of the object, leaving only the portion layered inside the hole and on top of the most recent layer.'''
    print("holeDevelop Start")
    layerThickness.append(layer_thickness)                                      #Keeps track of the new layer thickness
    #highestPoint = sp.get_highest_point(False,False)
    highestPoint, highestObj = sp.get_highest_point(True,False)                 #Retrieves the highest Z value and the layer associated with it
    #print(highestObj.Label)
    tempDep = deposit(all_polygons_dict, outlineLayer, layer_thickness)            #Creates a temporary depositon to use as a "stamp" to form the features
    depHighPoint = (sp.get_highest_point(False,False) - 1)/layer_thickness      #-1 for the deposition thickness, gives total number of cuts needed below Z placement
    tempDepAdjust = tempDep.Shape.copy()                                       #Copies of deposition, needed for forming the features
    tempDep2 = tempDep.Shape.copy()                                            #Copies of deposition, needed for forming the features
    overObjects = []
    lowPointLayer = holeLIL[-1].Shape.Vertexes[0].Point[2]                      #Lowest Z point for layer depositing onto
    upShifts = (highestPoint-lowPointLayer)/layer_thickness                     #Gives total number of necessary cuts (above Z) based off the thickness of the layer to deposit on
    for f in range(0,len(all_polygons_dict[layerNum])):                         #Goes through all polygons in given key (layerNum)
        polyLayer = sp.get_xy_points(all_polygons_dict[layerNum][f])            #Converts all to mm
        for point in polyLayer:
            point.append(0)
        print("Before layerDevelop Object")                                     #For debugging
        '''Below section creates a face from the vertices and then extrudes it to create the feature, it then creates a new FreeCAD Part'''
        pts2=[]
        for i in range(0,len(polyLayer)):                                       #Used to create an array of the "Vector points" required in FreeCAD
            pts2.append(FreeCAD.Vector(polyLayer[i][0],polyLayer[i][1],polyLayer[i][2])) #FreeCAD.Vector(x,y,z)
        wire=Part.makePolygon(pts2)                                             #Connects all points given above, makes a wire polygon (just a line)
        face=Part.Face(wire)                                                    #Creates a face from the wire above
        if bias != 0:                                                           #If a bias has been given then create a new face
            face = sp.biasFeatures(face, bias)                                  #Calls function that biases the feature and returns a new face
        overObjects.append(face.extrude(Base.Vector(0,0,highestPoint+layer_thickness)))
    '''
    The below section takes the copied deposition layer and shifts it down cutting out the features of the objects. It then takes the other copy and shifts
    it up to shape the top have of the new objects. The new objects are then passed to the hole tapering function.
    '''
    for i in range(0,int(math.ceil(depHighPoint/layer_thickness))):             #Shift down the number of times necessary to shape the lower half of the object
        tempDepAdjust.Placement.move(FreeCAD.Vector(0,0,-layer_thickness))
        #Part.show(tempDepAdjust)
        for idx,obj in enumerate(overObjects):
            overObjects[idx] = overObjects[idx].cut(tempDepAdjust)#obj = obj.cut(tempDepAdjust)#.Shape)
    #tempDep2.Placement.move(FreeCAD.Vector(0,0,layer_thickness))
    #Part.show(tempDep2)
    totalUpShifts = (int(math.ceil(upShifts))+len(holeLIL))
    for i in range(0,totalUpShifts):
        if i == 0:
            tempDep2.Placement.move(FreeCAD.Vector(0,0,layer_thickness))#+.0005))
            #for idx,obj in enumerate(overObjects):
            #    overObjects[idx] = overObjects[idx].cut(tempDep2)
            #tempDep2.Placement.move(FreeCAD.Vector(0,0,layer_thickness-.0005))
        else:
            tempDep2.Placement.move(FreeCAD.Vector(0,0,layer_thickness))
        #if "myPlanar" != lastDeposited[-2].Label:
        #    Part.show(tempDep2)
        #Part.show(tempDep2)
        for idx,obj in enumerate(overObjects):
            overObjects[idx] = overObjects[idx].cut(tempDep2)#obj = obj.cut(tempDep)#.Shape)
            #Part.show(overObjects[idx])
    for idx, newObj in enumerate(overObjects):
        extrusionLIL1.append(newObj)
        featureNames.append("myFeature"+str(len(featureNames)))                 #Creates new feature name
        featureLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", featureNames[-1])) #Creates new feature inside FreeCAD
        featureLIL1[-1].Shape = extrusionLIL1[-1]                               #Adds the feature as the newly "stamped" face
        print("Before Chamfer")                                                 #For debugging
        #if "myPlanar" == lastDeposited[-2].Label:
        #if idx == 3:
        #if "myPlanar" == lastDeposited[-2].Label:
        #    taperOverHoles(featureLIL1[-1], layer_thickness, angle, highestObj)
        #elif idx == 2:
        loop1Break = False; loop2Break = False#; loop3Break = False
        curvedCall = False
        bottomFaces = []
        for face in featureLIL1[-1].Shape.Faces:                                #Searches all the faces in the passed polygon looking for just bottom faces
            for idx, vert in enumerate(face.Vertexes):
                if idx == (len(face.Vertexes)-1) and round(vert.distToShape(highestObj.Shape)[0],2)==0:  #If the face intersects with the deposition layer then it is at the bottom
                    faceSurface = face.Surface
                    pt=Base.Vector(0,1,0)
                    param = faceSurface.parameter(pt)
                    #print(param)
                    norm = face.normalAt(param[0],param[1])
                    #print(norm)
                    if abs(norm[2]) != 0:                                       #If the face is oriented to one of the sides then ignore it
                        bottomFaces.append(face)                        #Append this face to our list, using list versus fusing them because we want all seperate faces
                        #Part.show(face)                                        #Used for debugging, currently shows the correct bottom faces
                elif round(vert.distToShape(highestObj.Shape)[0],2)==0 and (round(vert.Point[2],2) >= z_value[-1]):     #If the entire array has not been inspected then inspect next edge
                    continue
                else:
                    #print("breaking with z value of {:.2f} and height of {:.2f}".format(z_value[-1], vert.Point[2]))   #For debugging
                    break
        for face in bottomFaces:
            for edge1 in face.Edges:#featureLIL1[-1].Shape.Edges:
                edge1Dir = np.array(edge1.tangentAt(edge1.FirstParameter))      #Finds the vector direction of the edge and converts to a numpy array
                #Part.show(edge1)
                for edge2 in face.Edges:#featureLIL1[-1].Shape.Edges:
                    edge2Dir = np.array(edge2.tangentAt(edge2.FirstParameter))  #Finds the vector direction of the edge and converts to a numpy array
                    #Part.show(edge2)
                    #If any of the edges are not at right angles to each other then consider it unable to be chamfered
                    if edge1.firstVertex().Point[2] == edge1.lastVertex().Point[2] == edge2.firstVertex().Point[2] == edge2.lastVertex().Point[2]:
                        cornerAngle = math.degrees(math.acos(np.clip(np.dot(edge1Dir, edge2Dir)/ (np.linalg.norm(edge1Dir)* np.linalg.norm(edge2Dir)), -1, 1)))/90
                        #print(angle)
                        if math.ceil(cornerAngle) != math.floor(cornerAngle):#isinstance(angle, int) == False and angle != 0.0:
                            print("Non-rectangular object found, skipping taper")
                            chamfNames.append("newChamf"+str(len(chamfNames)))                                     #Creates new chamfer name for the fixed object
                            chamfLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", chamfNames[-1]))    #Creates new feature inside FreeCAD, must be feature and not a chamfer
                            chamfLIL1[-1].Shape = featureLIL1[-1].Shape
                            #holeSections = chamfLIL1[-1].Shape.cut(polygon.Shape)
                            loop1Break = True; loop2Break = True#; loop3Break = True
                            curvedCall = True
                            break
                        #else:
                        #    print("Continuing")
                if loop2Break == True:
                    break
            if loop1Break == True:
                break
        if curvedCall == False:
            taperOverHoles(featureLIL1[-1], layer_thickness, angle, highestObj)
        else:
            print("Object was Non-rectangular and did not get chamfered")
            #try:
                #taperOverHoles(featureLIL1[-1], layer_thickness, angle, highestObj)
                #taperNonRectangularObjects(featureLIL1[-1], layer_thickness, angle, highestObj)
            #except:
                #print("Failed regular taper")
            #taperNonRectangularObjects(featureLIL1[-1], layer_thickness, angle, highestObj)
        print("After Chamfer")                                                  #For debugging
    '''
    The below section cleans up the extra deposition layer created to shape the new objects. The new objects are then fused into a single layer and returned.
    This layer is used in several other functions and is the only object displayed in FreeCAD.
    '''
    FreeCAD.ActiveDocument.removeObject(depositLIL[-1].Label)
    depositLIL.pop()                                                            #Deletes old object
    depositNames.pop()                                                          #Deletes old object
    lastDeposited.pop()                                                         #Deletes old object
    z_value.append(z_value[-1]+layer_thickness)#-.0001)                         #Updates z_value to next height for building onto -*update for uneven features*

    featureCopies = []
    for obj in FreeCAD.ActiveDocument.Objects:                                  #Loops all objects
        #if "myFeature" in obj.Label:#"newChamf" in obj.Label:                  #If label is not substrate
        if "newChamf" in obj.Label:
            featureCopies.append(obj.Shape)                                     #For debugging
    layerCopy = featureCopies[0]                                                #Start out with just the first copied layer
    for feature in featureCopies[1:]:                                           #Add subsequent layers to first copied layer
        layerCopy = layerCopy.fuse(feature)                                     #Fuse combines all features together
    layerNames.append("myLayer"+str(len(layerNames)))                           #Creates new feature name
    layerLIL.append(FreeCAD.ActiveDocument.addObject("Part::Feature", layerNames[-1])) #Creates new feature inside FreeCAD
    layerLIL[-1].Shape = layerCopy                                              #Adds previous extrusion and the feature shape'''
    print("layerDevelop End")                                                   #For debugging
    lastDeposited.append(layerLIL[-1])
    print("holeDevelop End")
    return layerLIL[-1]

def layerName(layer_string): #Gets passed a string holding the layer specification as specified in the gds (txt) file
    return "layer"+str(layer_string.split("/")[0])

def isFloat(num): #Determines if the passed variable can be cast as a float
    try:
        i = float(num)
    except:
        return False
    return True


def isInt(num): #Determines if the passed variable can be cast as an int
    try:
        i = int(num)
    except:
        return False
    return True

def tempXSReader(filepath,all_polygons_dict, outputPath, lyp_info):
    '''Layer thickness must be the first argument inside of the etch arguments
    Grow function is not currently implemented
    Taper does not work for all objects, more complex objects mess up
    Circular objects do not work properly yet
    Missing additional features for etch function (commands from XS scripts)
    Need to add additional catch features for other commands that XS scripts can have

    Should turn these arrays into dictionaries
    '''
    print("evaluate_xs_file Begin")                         #For debugging
    outlineHold = [[0,0],[0,0]]
    for poly in all_polygons_dict:
        outline = sp.getOutlineValues(all_polygons_dict[poly][0])#layer[0])
        if outline[0] < outlineHold[0] or outline[1] > outlineHold[1]:
            outlineHold = [outline[0],outline[1]]
            outlineLayer = poly
    print(outlineHold)
    print(outlineLayer)
    #return
    with open(filepath) as myfile:                      #Opens and closes file from gds2 Filepath
        text = myfile.readlines()                       #Reads all lines, line by line
    depositLine = False
    depositions = []
    deposit_thickness = 0
    layer_thickness = 0
    varNames = []
    #layerNames = []
    xsLayerNames = []
    xsVariables = []
    for counter, line in enumerate(text):
        #print(counter+1)
        #print("Executing line number %d: %s" % ((counter+1),line))
        line = line.replace(" ","") #Removes all the spaces
        if (line[0] == "#") or (line.isspace() == True): #If line is a comment or blank then skip it
            print("Skipping line number %d" % (counter+1))
            continue
        print("Executing line number %d: %s" % ((counter+1),line))
        if depositLine == True and (counter != len(text)-1): #Checks to see if a deposition is actually needed
            if "planarize" in text[counter+1]:
                depositLine = False
                continue
            #if "inverted" in line:
            #    depositLine = False
            if "deposit" in line:#(line[0] == "#") and ("inverted" not in line): #If not doing a layer deposit next (used with .inverted) then make the deposition
                print("Running Deposition")
                #depositions.append(deposit(all_polygons_dict, "layer12", deposit_thickness)) #Might not always be layer12
                #print("Executing: %s" % line)
                #varNames.append([text[counter-1].split("=")[0],deposit(all_polygons_dict, "layer12", deposit_thickness)]) #[dep name, dep obj]
                varNames.append([line.split("=")[0],deposit(all_polygons_dict, outlineLayer, deposit_thickness)]) #[dep name, dep obj]
                depositLine = False
                continue
            if "planarize" in line:
                depositLine = False #Skip this deposit since it is getting planarized'''
        '''Below runs through each line in the XS script and determines how to run it within this program'''
        if "depth(" in line: #Empty function not used in FreeCAD
            continue
        elif "height(" in line: #Empty function not used in FreeCAD
            continue
        elif "delta(" in line: #Empty function not used in FreeCAD
            continue
        elif "dbu" in line: #Empty function not used in FreeCAD
            continue
        elif "bulk" in line: #Initial substrate generation
            #text[counter] = line.replace("bulk","bulk.bulk()")
            substrate = bulk.bulk(all_polygons_dict,outlineLayer)
        elif "layer(" in line: #Some layer function setting initial names, do we need this right now?
            #print("Incomplete, but do we need these layer names?")
            xsLayerNames.append([line.split("=")[0],0])
            print(layerName(line.split("\"")[1].split(")")[0]))
            xsLayerNames[-1][1] = layerName(line.split("\"")[1].split(")")[0])
            #print(xsLayerNames[-1])
        elif "deposit(" in line: #Asking for a deposition, might be for building a layer
            print("Found Deposition")
            depositLine = True
            #deposit_thickness = eval(line.split("(")[1].split(")")[0]) #Should pull variale from in between parenthesis
            lineVar = line.split("(")[1].split(")")[0]
            varNames.append([line.split("=")[0],0])
            for idx, var in enumerate(xsVariables):
                if str(var[0]) == str(lineVar):
                    deposit_thickness = xsVariables[idx][1]
                    break
            #varNames.append([line.split("=")[0],deposit(all_polygons_dict, outlineLayer, deposit_thickness)]) #[dep name, dep obj]
        elif "etch(" in line:#elif line[0:4] == "mask": #If mask being called, meaning a feature addition is being made
            etchArg = line.split("etch(")[1]
            #layer_thickness = etchArg.split(",")[0] #Taking this as  first argument
            #xslayerName = line.split("mask(")[1].split(")")[0]
            thickVar= etchArg.split(",")[0]
            layVar = line.split("mask(")[1].split(")")[0].replace(".inverted", "")
            for idx, var in enumerate(xsVariables):
                if str(var[0]) == str(thickVar):
                    layer_thickness = float(xsVariables[idx][1])
                    break
            for idx, var in enumerate(xsLayerNames):
                #print("Comparing " + str(var[0]) + " to " +str(layVar))
                if str(var[0]) == str(layVar):
                    xslayerName = xsLayerNames[idx][1]
                    break
            print("Lay thick is %s and xslayerName is %s" % (layer_thickness, xslayerName))
            if "taper" in etchArg:
                ang = etchArg.split(":taper=>")[1].split(",")[0]
                print(ang)
                angle = math.pi*float(ang)/180
            else:
                angle = 0 #Need to implement this into the layerDevelop function
            if "bias" in etchArg:
                #biasVal = etchArg.split(":bias=>")[1].split(",")[0]
                biasVar= etchArg.split(":bias=>")[1].split(",")[0]
                for idx, var in enumerate(xsVariables):
                    if str(var[0]) == str(biasVar):
                        biasVal = float(xsVariables[idx][1])
                        break
            else:
                biasVal = 0
            print(line)
            if "inverted" in line: #Feature depositions
                if len(holeLIL) == 0: #If no holes have been made yet
                    print("No holes before deposition")
                    #layerDevelop(all_polygons_dict, xslayerName, layer_thickness, angle, biasVal)
                    #varNames.append([text[counter-1].split("=")[0],layerDevelop(all_polygons_dict, xslayerName, layer_thickness, angle, biasVal)])
                    for idx, grouping in enumerate(varNames):
                        if grouping[1] == 0:
                            varNames[idx][1] = layerDevelop(all_polygons_dict, xslayerName, layer_thickness, angle, biasVal)
                            break
                    sp.remove_objs()
                else:
                    #print(angle)
                    print(xslayerName, layer_thickness, angle, biasVal)
                    #holeDevelop(all_polygons_dict, xslayerName, layer_thickness, angle, outlineLayer, biasVal)
                    for idx, grouping in enumerate(varNames):
                        if grouping[1] == 0:
                            varNames[idx][1] = holeDevelop(all_polygons_dict, xslayerName, layer_thickness, angle, outlineLayer, biasVal)
                            break
                    sp.remove_objs()
            else: #Hole creation
                if "into" in etchArg:
                    holeLayName = etchArg.split(":into=>")[1].split(")")[0]
                    for idx, var in enumerate(varNames):
                        print("Comparing " + str(var[0]) + " to " +str(holeLayName))
                        if str(var[0]) == str(holeLayName):
                            holeLay = varNames[idx][1]
                            #print(holeLay.Label)
                            break
                else:
                    print("Missing the layer to cut into")
                if len(holeLIL) > 0 and biasVal != 0: #Takes into account the effects of depositions being .0005 off (gets rid of a lip that forms between multi-layer holes)
                    biasVal = biasVal #- .0006
                print(xslayerName, holeLay.Label, layer_thickness, biasVal)
                #print(depositLIL[-2].Label)
                #holeCreation(all_polygons_dict, "layer3", layer_thickness,  math.pi*45/180,depositLIL[-2], 0)
                holeCreation(all_polygons_dict, xslayerName, layer_thickness, angle, holeLay, biasVal)#depositLil and layer3 need to become holeLay and xslayerName
        elif "planarize" in line: #Currently only set up for 1 planarized layer, can easily make more by turning planarLay variable into an array
            maxZ, topObj = sp.get_highest_point(True, False)
            planarLay = planar.planarize(topObj.Label)#, allObj)#layerLIL[-1].Label)#topObj.Label)
            varNames.append([line.split("=>")[1].split(",")[0],planarLay])
            maxZ = sp.get_highest_point(False,False)
            z_value.append(maxZ)
            lastDeposited.append(planarLay)
            sp.remove_objs()
        elif "output" in line:
            print("Incomplete, but might not be necessary?")
        else: #This should evaluate any of the other lines that have variable definitions
            line = line.rstrip()
            xsVariables.append([line.split("=")[0],0])
            xsVariables[-1][1] = line.split("=")[1]
            if isInt(xsVariables[-1][1]):
                xsVariables[-1][1] = int(xsVariables[-1][1])
            elif isFloat(xsVariables[-1][1]):
                xsVariables[-1][1] = float(xsVariables[-1][1])
            else:
                inlineVariables = []
                inlineOperations = []
                expression  = line.split("=")[1]
                for idx, vari in enumerate(xsVariables):
                    #print("Vari to check "+str(vari[0]))
                    if str(vari[0]) in expression:
                        #print(vari)
                        #print("Found variable "+str(vari[0]))
                        inlineVariables.append(str(vari[0]))
                        expression = expression.replace(str(vari[0]),str(xsVariables[idx][1]))
                        #print("Final expression " +expression)
                xsVariables[idx][1] = float(eval(expression))#eval(str(exec(expression)))
    for rename in varNames:
        featureLIL1.append(FreeCAD.ActiveDocument.addObject("Part::Feature", rename[0])) #Creates new feature inside FreeCAD
        featureLIL1[-1].Shape = rename[1].Shape
        FreeCAD.ActiveDocument.removeObject(rename[1].Label)
    objToDel = []
    possibleColors = [(0.0,0.0,0.0),(1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0),(1.0,1.0,0.0),(1.0,0.0,1.0),(0.0,1.0,1.0),\
        (1.0,1.0,1.0),(0.36,0.82,0.37),(0.5,0.5,0.2),(0.7,0.3,0.2),(0.1,0.7,0.5),\
        (0.5,0.7,0.9),(0.9,0.9,0.1),(0.2,0.5,0.7),(0.3,0.9,0.2),(0.5,0.1,0.7),(0.8,0.2,0.1),(0.3,0.3,0.3)]
    random.seed() #Used for color generation, if needed
    if lyp_info != "":
        #print(lyp_info)
        totLypInfo = len(lyp_info.items())-1
    for idx, obj in enumerate(FreeCAD.ActiveDocument.Objects):
        if "myLayerHole" in obj.Label:
            #FreeCAD.ActiveDocument.getObject(obj.Label).Visibility = False
            obj.Visibility = False
        if obj.Visibility == True:
            if lyp_info != "":
                for num, layer in enumerate(lyp_info.items()):
                    if layer[1][0].lower() in obj.Label:
                        #print("Hello "+obj.Label)
                        h = layer[1][1].lstrip('#')
                        #print('RGB =', tuple(float(int(h[i:i+2], 16)/255) for i in (0, 2, 4)))
                        Gui.ActiveDocument.getObject(obj.Label).ShapeColor = tuple(float(int(h[i:i+2], 16)/255) for i in (0, 2, 4))
                        #Gui.ActiveDocument.getObject(obj.Label).ShapeColor = tuple(list(Gui.ActiveDocument.getObject(obj.Label).ShapeColor)[0:3])
                        #print(Gui.ActiveDocument.getObject(obj.Label).ShapeColor)
                        break
                    elif num == totLypInfo:
                        if idx == len(possibleColors)-1: #If more objects than current colors, create another one
                            r = random.randint(0,255)/255
                            g = random.randint(0,255)/255
                            b = random.randint(0,255)/255
                            possibleColors.append((r,g,b))
                        #print("Goodbye "+obj.Label)
                        Gui.ActiveDocument.getObject(obj.Label).ShapeColor = possibleColors[idx]
            else:
                if idx == len(possibleColors)-1: #If more objects than current colors, create another one
                    r = random.randint(0,255)/255
                    g = random.randint(0,255)/255
                    b = random.randint(0,255)/255
                    possibleColors.append((r,g,b))
                #print("Goodbye "+obj.Label)
                Gui.ActiveDocument.getObject(obj.Label).ShapeColor = possibleColors[idx]
            #for layer in
            #obj.ShapeColor = possibleColors[idx]
            #Gui.ActiveDocument.getObject(obj.Label).ShapeColor = possibleColors[idx]
        else:
            objToDel.append(obj.Label)
    for delIndex in objToDel:
        FreeCAD.ActiveDocument.removeObject(delIndex)
    if outputPath != "":
        for obj in FreeCAD.ActiveDocument.Objects:
            finalPath = outputPath+"/"+obj.Label+".step"
            Part.export([obj], finalPath)#'D:/testfiles/mymodel.stl')
    print("evaluate_xs_file End")                         #For debugging


class Inputs(QtGui.QDialog):
    inputFiles = [""]*3
    def __init__(self):
        super(Inputs, self).__init__()
        self.initUI()
    def initUI(self):
        gdsInput = QtGui.QPushButton("GDS2 File (.txt)")
        gdsInput.clicked.connect(self.gdsInputClicked)
        lypInput = QtGui.QPushButton("LYP File (.lyp)")
        lypInput.clicked.connect(self.lypInputClicked)
        xsInput = QtGui.QPushButton("XS Script (.xs)")
        xsInput.clicked.connect(self.xsInputClicked)
        done = QtGui.QPushButton("Finished")
        done.clicked.connect(self.finished)
        #
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        buttonBox.addButton(gdsInput, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(lypInput, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(xsInput, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(done, QtGui.QDialogButtonBox.ActionRole)
        #
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        # define window		xLoc,yLoc,xDim,yDim
        self.setGeometry(	250, 250, 0, 50)
        self.setWindowTitle("Select the Input Files")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    def gdsInputClicked(self):
        filename, filter = QtGui.QFileDialog.getOpenFileName(parent=self, caption='Open file', dir=dir_path, filter='*.txt')
        if filename:
            self.inputFiles[0] = filename
    def lypInputClicked(self):
        filename, filter = QtGui.QFileDialog.getOpenFileName(parent=self, caption='Open file', dir=dir_path, filter='*.lyp')
        if filename:
            self.inputFiles[1] = filename
    def xsInputClicked(self):
        filename, filter = QtGui.QFileDialog.getOpenFileName(parent=self, caption='Open file', dir=dir_path, filter='*.xs')
        if filename:
            self.inputFiles[2] = filename
    def finished(self):
        if self.inputFiles[0] == "":
            reply = QtGui.QMessageBox.information(None,"","Please select a gds2 (.txt) file.")
            self.gdsInputClicked()
        if self.inputFiles[2] == "":
            reply = QtGui.QMessageBox.information(None,"","Please select a XS script (.xs).")
            self.xsInputClicked()
        self.close()

class Exports(QtGui.QDialog):
    def __init__(self):
        super(Exports, self).__init__()
        self.initUI()
    def initUI(self):
        affirmative = QtGui.QPushButton("Affirmative")
        affirmative.clicked.connect(self.affirmativeClicked)
        negative = QtGui.QPushButton("Negative")
        negative.clicked.connect(self.negativeClicked)
        #
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        buttonBox.addButton(affirmative, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(negative, QtGui.QDialogButtonBox.ActionRole)
        #
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        # define window xLoc,yLoc,xDim,yDim
        self.setGeometry(250, 250, 350, 50)
        self.setWindowTitle("Export objects as STEP files?")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def affirmativeClicked(self):
        reply = QtGui.QMessageBox.information(None,"","Please select an output folder.")
        directoryName = QtGui.QFileDialog.getExistingDirectory(parent=self, caption='Select Directory', dir=dir_path)
        if directoryName:
            self.outputFiles = directoryName
            self.retStatus = 1
            self.close()
        else:
            reply = QtGui.QMessageBox.information(None,"","Please select an output folder.")
            self.affirmativeClicked()
    def negativeClicked(self):
        reply = QtGui.QMessageBox.information(None,"","No automatic exports will be made.")
        self.outputFiles = ""
        self.close()

if __name__ == "__main__":
    print("Program Begin")
    fileIn = Inputs()
    fileIn.exec_()
    gds2Filepath = fileIn.inputFiles[0]
    all_polygons_dict = files.extract_gds2_info(gds2Filepath)
    if fileIn.inputFiles[1] != "":
        lypFilepath = fileIn.inputFiles[1]#Layer properties file
        lyp_info = files.get_lyp_data(lypFilepath)
    else:
        lyp_info = ""
    xsFilepath = fileIn.inputFiles[2]#xs file
    #print(gds2Filepath)
    #print(lypFilepath)
    #print(xsFilepath)
    fileOut = Exports()
    fileOut.exec_()
    exportPath = fileOut.outputFiles
    App.newDocument("Conversion") #Creates new FreeCAD document
    #print(lyp_info)
    tempXSReader(xsFilepath, all_polygons_dict, exportPath, lyp_info)
    print("Program End")

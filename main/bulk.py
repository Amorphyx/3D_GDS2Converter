import Part, PartGui                                                            #Required for using FreeCAD parts
from FreeCAD import Base                                                        #Required for some functions in freecad
import FreeCAD
import FreeCADGui
import sys, importlib                                                           #Used for importing and reloading modules
try:                                                                            #Only runs reload if it is needed
    importlib.reload(sys.modules['supporting_functions'])                    #Reloads any changes in modules
except:
    print("Reload not needed for supporting_functions")
import supporting_functions as sp

def bulk(all_polygons_dict, layerNum):                                                    #Creates the base layer (substrate)
    '''
    The bulk function creates the lower substrate on the design based on the outline of the design.

    Passed the dictionary containing all the polygons and the outline polygon layer

    Returns the substrate shape
    '''
    print("bulk start")                                                         #For debugging
    if FreeCAD.ActiveDocument.Objects == []:                                    #Checks for no objects in FreeCAD
        print("Before Substrate")
        poly1 = sp.get_xy_points(all_polygons_dict[layerNum][0])                #Gets the outside points of the bottom layer **NEEDS UPDATING
        for point in poly1:
            point.append(0.0)                                                   #Attaches a Z componenet to every vertex
        pts=[]
        for i in range(0,len(poly1)):                                           #Runs through all verticies
            pts.append(FreeCAD.Vector(poly1[i][0],poly1[i][1],poly1[i][2]))     #pts.append(App.Vector(X,Y,Z))
        wire=Part.makePolygon(pts)                                              #Creates just a boundary
        face=Part.Face(wire)                                                    #Makes a face for a solid object
        subExtrusion = face.extrude(Base.Vector(0,0,-3.0))                      #Creates extrusion for object, -3 is arbitrary
        substrate = FreeCAD.ActiveDocument.addObject("Part::Feature", "Substrate")
        substrate.Shape = subExtrusion
    else:
        print("A substrate already exists and another cannot be generated.")
    print("bulk end")                                                           #For debugging
    return substrate.Shape

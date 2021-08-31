import Part, PartGui                                                            #Required for using FreeCAD parts
from FreeCAD import Base                                                        #Required for some functions in freecad
import FreeCAD
import FreeCADGui
import sys, importlib                                                           #Used for importing and reloading modules
try:                                                                            #Only runs reload if it is needed (not needed on first run through)
    importlib.reload(sys.modules['supporting_functions'])                    #Reloads any changes in modules
except:
    print("Reload not needed for supporting_functions")
import supporting_functions as sp

#planarNames = []                                                                #Can be used to hold the names of multiple planarized layers
#planarLIL = []                                                                  #Can be used to hold multiple planar layer objects

def planarize(layerNum):                                                        #Creates a single Z valued layer covering all previous features
    '''
    planarize function takes the passed FreeCAD function name and finds the distance from that shape to the substrate. It then finds the highest
    point (top of a feature) and takes that point minus the base of the passed layer which gives the total height of the top object. From here an additional
    "buffer" is added to those values (so that all features are properly covered - and required for FreeCAD to evaluate properly) to create a total extrusion
    distance. A layer is then created using the outermost bounds of the FreeCAD document (substrate/outline layer) and the total extrusion distance.
    The new layer is then trimmed of all objects (not substrate) in the FreeCAD document (anything already deposited). The final object will rest on top of
    all the other layers as long as there are no gaps within the other layers (these will get filled in with this object).

    Function is passed the name of the top layer

    Returns the planarized layer

    **Currently only designed to create one planarization; however, FreeCAD will automatically append numbers to the name if additional planar layers are called.
    This can also be updated to use the two global arrays (currently commented out).
    '''
    print("Start planarize")
    layerObj = FreeCAD.ActiveDocument.getObject(layerNum).Shape
    belowLayer = layerObj.Edges[0].distToShape(FreeCAD.ActiveDocument.getObject("Substrate").Shape)[0]
    additionalPlanarizeLevel = 1                                                #Can change this to add extra thickness to the planarization
    maxHeight = round(sp.get_highest_point(),4)
    objHeight = maxHeight - round(layerObj.Vertexes[0].Point[2],4)              #Returns the max height of just the object being planarizized
    totalExtrusion = belowLayer+objHeight+additionalPlanarizeLevel              #Total value needed to extrude the planar layer
    outerBounds = list(sp.get_2D_outer_bounds())
    outerBounds.append(outerBounds[0])                                          #Closes the shape by reconnecting the last vertex to the first vertex
    for idx, point in enumerate(outerBounds):
        outerBounds[idx] = list(outerBounds[idx])                               #Changes the tuple values into a list so they can be edited
        outerBounds[idx].append(0)                                              #Starting Z value of 0
    #print(outerBounds)
    pts=[]
    for pt in outerBounds:
        pts.append(FreeCAD.Vector(pt[0],pt[1],pt[2]))
    planarWire = Part.makePolygon(pts)                                          #Makes a wire out of the outermost bounds
    planarFace = Part.Face(planarWire)
    planarExtrusion = planarFace.extrude(Base.Vector(0,0,totalExtrusion))#+.0005)) #Might need to add a small amount, like .0005, here to account for the subtraction done later on
    cutObj = planarExtrusion.copy()                                             #Used to trim the planar layer
    for obj in FreeCAD.ActiveDocument.Objects:                                  #Loops all objects
        if obj.Label != "Substrate":                                            #If FreeCAD label is not substrate
            #print(obj.Label)                                                   #For debugging
            planarExtrusion = planarExtrusion.cut(obj.Shape)                    #Takes the original "block" planar layer and cuts out all features/layers
    #Part.show(planarExtrusion)                                                 #For debugging
    cutObj.Placement.move(FreeCAD.Vector(0,0,totalExtrusion))#+.0006)) #The .0006 accounts for the -.0005 movement later on and allows for all extra edges to be deleted
    trimmedPlanar = planarExtrusion.cut(cutObj)                                 #Trims the top of the planar layer to ensure proper height and being flat
    planarLayer = FreeCAD.ActiveDocument.addObject("Part::Feature", "myPlanar")
    planarLayer.Shape = trimmedPlanar
    print("End planarize")
    return planarLayer

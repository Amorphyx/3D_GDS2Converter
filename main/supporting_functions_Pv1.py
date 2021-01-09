import Part, PartGui                                                            #Required for using FreeCAD parts
from FreeCAD import Base                                                        #Required for some functions in freecad
import FreeCAD
import FreeCADGui
import sys, importlib                                                           #Used for importing and reloading modules

class Polygon:                                                                  #Creates polygons with individual ids
    def __init__(self, xf, yf, idf):                                            #Initialize these three variables when creating class
        self.x = xf
        self.y = yf
        self.ids = idf                                                          #id is the layer name extracted from the gds2 file

def output(layer, features): #Incomplete function -Is it needed though? This function labels each layer, might not be useful in FreeCAD
    print("Output begin")
    '''
    # gets the layer info from the layer_spec
    if (layer =~ /^(\d+)$/): # is "l"?
        ls = "layer#{layer_spec}"
    elif (layer =~ /^(\d+)\/(\d+)$/): # is "l/d"?
        ls = "l/d"
        ls = layer_spec.split("/")[0]
        ls = "layer#{ls}"
    elif (layer_spec =~ /^(.*)\s*\((\d+)\/(\d+)\)$/): # is "n(l/d)"?
        ls = "n(l/d)"
        ls = layer_spec.split("/")[0].split("(")[1]
        ls = "layer#{ls}"
    else: # is "n"?
        ls = "layer#{layer_spec}"

    if !cmp: # check to make sure the component is valid
        raise " #{cmp} is not a valid component!"
    else: # assign the layer to the layer tag
        cmp.layer = @l2m_name[ls.to_sym]
    '''
    print("Output end")
    #return 0 #empty for now


def get_xy_points(polygon):                                                     #Converts the x and y data points from um to mm, returns unique x and y values
    print("get_xy_points Begin")                                                #For debugging
    pts = []                                                                    #Empty array to house x,y points
    for i in range(0,len(polygon.x)):
        x=polygon.x[i] /10                                                    #Start conversion to mm
        y=polygon.y[i] /10                                                    #This reduces inputs to FreeCAD units
        pts.append([x,y])
    print("get_xy_points end")                                                  #For debugging
    #print(pts)                                                                 #For debugging
    return pts


def get_2D_outer_bounds():                                                      #Gets the outermost bounds of the model, should be the substrate bounds generally
    print("get_2D_outer_bounds")                                                #For debugging
    '''
    # gets all components in the model
    componentsAll=FreeCAD.ActiveDocument.Objects
    all_points = []
    for obj in componetsAll:
        for vertex in obj.Shape.Vertexes
            all_points.append((vertex.Point.X,vertex.Point.Y))

    all_unique_points = list(set(all_points))
    '''
    all_points = [[vertex.Point for vertex in obj.Shape.Vertexes] for obj in FreeCAD.ActiveDocument.Objects]    #Grabs all vertices from all features
    flatten = lambda l: [item for sublist in l for item in sublist]                                             #Creates one array of all vertices
    all_points = flatten(all_points)                                                                            #Uses above one-line function
    #xs = list(set([point.X for point in all_points])); ys = list(set([point.Y for point in all_points]))       #Seperates x and y points
    xs = list(set([point[0] for point in all_points])); ys = list(set([point[1] for point in all_points]))      #Seperates x and y points
    x_min = min(xs); x_max = max(xs); y_min = min(ys); y_max = max(ys)                                          #Find the max and minimum values
    outer_bounds = [(x_min,y_min),(x_max,y_min),(x_max,y_max),(x_min,y_max)]                                    #Get the outer bounds of the model
    print("get_2D_outer_bounds end")                                                                            #For debugging
    return outer_bounds

def getOutlineValues(polygon):                                                  #Returns the lowest and highest points from the passed polygon, used to find the outline
    print("getOutlineValues Begin")                                             #For debugging
    all_points = []                                                             #Empty array to house x,y values
    for i in range(0,len(polygon.x)):
        x=polygon.x[i] /1000                                                    #Start conversion to mm
        y=polygon.y[i] /1000                                                    #This reduces inputs to FreeCAD units
        all_points.append([x,y])
    xs = list(set([point[0] for point in all_points])); ys = list(set([point[1] for point in all_points]))  #Seperates x and y points
    x_min = min(xs); x_max = max(xs); y_min = min(ys); y_max = max(ys)                                      #Find the max and minimum values
    #outer_bounds = [[x_min,y_min],[x_max,y_min],[x_max,y_max],[x_min,y_max]]                               #Get the outer bounds of the model
    outer_bounds = [[x_min,y_min],[x_max,y_max]]
    #print(outer_bounds)                                                        #For debugging
    print("getOutlineValues end")                                               #For debugging
    return outer_bounds

def get_highest_point(needObj = False, all = False):
    '''
    This function simply returns the highest vertex from all the points. If multiple vertices appear at the highest
    it only takes the one and returns it's Z value. The time complexity of this is awful, but it is brute forced.
    At some point this needs to be redone in a better method, but for small groups of objects it is okay.

    Passed two booleans: the first is used to determine if the object associated with the highest points is needed, and
    the second is used to determine if all objects at the max height are needed.

    3 possible return values:
    1) The max height (if both passed booleans false)
    2) The max height and the object it was found on (if needObj true)
    3) The max height, the object the height was found on, and any other objects that share that height (if both passsed booleans true)
    '''
    #Maybe make this one for loop?
    maxPoint = 0; allObjects = []
    for objects in FreeCAD.ActiveDocument.Objects:                              #Runs through all objects in the FreeCAD document
        for vertex in objects.Shape.Vertexes:
            if vertex.Point[2] > maxPoint:                                      #Could also use Edge.firstVertex().Point[2], Point has (x,y,z) so [0,1,2]
                maxPoint = vertex.Point[2]                                      #Updates current max height value
                maxHeightObj = objects                                          #Updates the highest object
    if all == True:                                                             #If all objects have been requested
        for objects in FreeCAD.ActiveDocument.Objects:                          #Runs through all objects in the FreeCAD document
            for vertex in objects.Shape.Vertexes:
                if vertex.Point[2] == maxPoint:                                 #Could also use Edge.firstVertex().Point[2], Point has (x,y,z) so [0,1,2]
                    allObjects.append(objects)
                    break
        return maxPoint,maxHeightObj, allObjects
    if needObj == True:
        return maxPoint,maxHeightObj
    elif needObj == False:
        return maxPoint

def topXY(X,Y,depLayer):
    '''
    This function takes a given X,Y point and finds the highest (+z) value associated with it. It creates a very small face, required for FreeCAD
    distToShape function, and then finds the distance to the top layer (which was the deposition that just occured).
    Inputs: X and Y coordinate; the string name of the highest deposition layer
    Returns: The Z value associated with the X and Y coordinate
    '''
    points = [FreeCAD.Vector(X,Y,50),FreeCAD.Vector(X-.01,Y,50),FreeCAD.Vector(X-.01,Y-.01,50),FreeCAD.Vector(X,Y-.01,50),FreeCAD.Vector(X,Y,50)]
    wire = Part.makePolygon(points)
    face = Part.Face(wire)
    height = face.distToShape(FreeCAD.ActiveDocument.getObject(depLayer).Shape)[0]
    Zval = 50 - height
    return Zval

def remove_objs():                                                              #Removes extra objects that are no longer needed
    labels = [obj.Label for obj in FreeCAD.ActiveDocument.Objects]
    for label in labels:
        if "myFeature" in label:
            FreeCAD.ActiveDocument.removeObject(label)
        if "tempObj" in label:
            FreeCAD.ActiveDocument.removeObject(label)
        if "SillyName" in label:
            FreeCAD.ActiveDocument.removeObject(label)
        if "NewObj" in label:
            FreeCAD.ActiveDocument.removeObject(label)
        if "newChamf" in label:
            FreeCAD.ActiveDocument.removeObject(label)
        if "myChamf" in label:
            FreeCAD.ActiveDocument.removeObject(label)
    #[FreeCAD.ActiveDocument.removeObject(label) for label in labels if "myFeature" in label]
    #[FreeCAD.ActiveDocument.removeObject(label) for label in labels if "tempObj" in label]
    #[FreeCAD.ActiveDocument.removeObject(label) for label in labels if "SillyName" in label]

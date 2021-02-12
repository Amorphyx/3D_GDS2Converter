import Part, PartGui                                                            #Required for using FreeCAD parts
from FreeCAD import Base                                                        #Required for some functions in freecad
import FreeCAD
import FreeCADGui
import sys, importlib                                                           #Used for importing and reloading modules
import numpy as np
import math
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
        x=polygon.x[i] /10                                                    #Start conversion to mm
        y=polygon.y[i] /10                                                    #This reduces inputs to FreeCAD units
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
        if objects.Visibility == True:                                          #This limits the scan to only objects that will be used for the final layers
            for vertex in objects.Shape.Vertexes:
                if vertex.Point[2] > maxPoint:                                  #Could also use Edge.firstVertex().Point[2], Point has (x,y,z) so [0,1,2]
                    maxPoint = vertex.Point[2]                                  #Updates current max height value
                    maxHeightObj = objects                                      #Updates the highest object
    if all == True:                                                             #If all objects have been requested
        if objects.Visibility == True:                                          #This limits the scan to only objects that will be used for the final layers
            for objects in FreeCAD.ActiveDocument.Objects:                      #Runs through all objects in the FreeCAD document
                for vertex in objects.Shape.Vertexes:
                    if vertex.Point[2] == maxPoint:                             #Could also use Edge.firstVertex().Point[2], Point has (x,y,z) so [0,1,2]
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
        if "tempChamf" in label:
            FreeCAD.ActiveDocument.removeObject(label)
    #[FreeCAD.ActiveDocument.removeObject(label) for label in labels if "myFeature" in label]
    #[FreeCAD.ActiveDocument.removeObject(label) for label in labels if "tempObj" in label]
    #[FreeCAD.ActiveDocument.removeObject(label) for label in labels if "SillyName" in label]

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

def biasFeatures(feature, bias):                                                #Uses edge comparisons to bias a passed face object
    '''
    This function is responsible for biasing (expanding or shrinking) a given object by a given amount. It does this by comparing edge distances and making
    the distances either larger or smaller through a series of comparisons.

    Inputs: the feature (face) being biased and the value to bias by. A negative bias value enlarges an object and a positive bias shrinks the object

    Returns: a new face object that has been biased
    '''
    print("Bias begin")                                                         #For Debugging
    print("bias = %f" % bias)                                                   #For debugging
    '''
    The below section gathers boundary conditions needed to correctly bias the objects. The points from the bounds variable are used to keep
    an object from being biased off of the given substrate (if applicable) and the loop finds the outside edge points of the feature
    '''
    bounds = get_2D_outer_bounds()                                              #Grabs the outermost bounds of the device
    xLow = bounds[0][0]; xHigh = bounds[2][0]; yLow = bounds[0][1]; yHigh = bounds[2][1] #Used later to not bias objects off the substrate
    Z = feature.Vertexes[0].Point[2]                                            #Gets the height value for the new face
    lowX = 0; highX = 0; lowY = 0; highY = 0                                    #Used to find the boundaries of the feature being biased
    for points in feature.Vertexes:                                             #Runs through every vertex and grabs the boundary points
        point = points.Point
        if point[0] < lowX:
            lowX = point[0]
        if point[0] > highX:
            highX = point[0]
        if point[1] < lowY:
            lowY = point[1]
        if point[1] > highY:
            highY = point[1]
    xVals = []; yVals = []                                                      #Used to keep track of the new vertex points
    #print(len(feature.Edges))                                                  #For debugging
    '''
    The below section is divided into two categories: simple rectangular objects with 4 edges, and more complex objects with an even number of edges.
    The biasing works by taking an edge and checking it's distance to an edge on the opposite side of the object (by checking vector direction of the edges).
    It then shifts the edge by the biasing amount and checks to see if it shifted in the right direction. If not then it'll take the values being shifted the
    other direction. For more complex objects the edge being compared to will always be an outside edge since an inside edge might actually need to be shifted
    towards another inside edge for the object to get larger. The new vertices are recorded onto 2 arrays, 1 for the x values and 1 for the y values. These
    are updated independently since right now all biases are done on axis (all inputs expected to exist on axis). So, one edge will move only in the x direction
    and will create updated x values for the vertices and then the next edge will move in the y direction and create updated y values for the vertices.
    edge1 is always the edge that will undergo the bias and edge2 is always the edge that it is being compared to.

    **Will have to be updated for any objects with an odd number of edges (including "circular" objects). Will have to be updated for off-axis objects.
    '''
    if len(feature.Edges) == 4:                                                 #If rectangular with only 4 edges
        #print("TRUE")                                                          #For debugging
        for edge1 in feature.Edges:                                             #Runs through every edge of the passed feature
            edge1First = edge1.firstVertex().Point; edge1Last = edge1.lastVertex().Point    #Gets the two vertices of the edge
            if (edge1First[0] == edge1Last[0] == lowX == xLow) or (edge1First[0] == edge1Last[0] == highX == xHigh):    #If the edges are at the boundary of the device
                xVals.append(edge1First[0])                                     #Don't add any bias since edge at boundary of device
                xVals.append(edge1Last[0])                                      #Don't add any bias since edge at boundary of device
                if len(yVals) == 0:                                             #If no y values have been updated then add a value (used to balance vertices)
                    yVals.append(0)                                             #5 vertices required to close an object, this gives the fifth vertex
                continue                                                        #Continue to next edge
            if (edge1First[1] == edge1Last[1] == lowY == yLow) or (edge1First[1] == edge1Last[1] == highY == yHigh):#If the edges are at the boundary of the device
                yVals.append(edge1First[1])                                     #Don't add any bias since edge at boundary of device
                yVals.append(edge1Last[1])                                      #Don't add any bias since edge at boundary of device
                if len(xVals) == 0:                                             #If no x values have been updated then add a value (used to balance vertices)
                    xVals.append(0)                                             #5 vertices required to close an object, this gives the fifth vertex
                continue                                                        #Continue to next edge
            #print(edge1.firstVertex().Point[0], edge1.lastVertex().Point[0])   #For debugging
            edge1Dir = np.array(edge1.tangentAt(edge1.FirstParameter))          #Finds the vector direction of the edge and converts to a numpy array
            for edge2 in feature.Edges:                                         #Runs through all the edges of the feature to find a comparison edge
                edge2Dir = np.array(edge2.tangentAt(edge2.FirstParameter))      #Finds the direction of the second edge
                #Below line takes the dot product of the two edge directions. If they are exactly opposite directions then the angle will be 180 degrees
                if math.degrees(math.acos(np.dot(edge1Dir, edge2Dir) / (np.linalg.norm(edge1Dir)* np.linalg.norm(edge2Dir)))) == 180:
                    #Part.show(edge1)                                           #For debugging
                    #Part.show(edge2)                                           #For debugging
                    #print(edge1Dir)                                            #For debugging
                    #print(edge2Dir)                                            #For debugging
                    origDist = edge1.distToShape(edge2)[0]#np.linalg.norm(edge1-edge2) #Finds the original distance between the two FreeCAD edges
                    tempPts = [FreeCAD.Vector(edge1First[0]+bias, edge1First[1], Z), \
                                FreeCAD.Vector(edge1Last[0]+bias,edge1Last[1], Z)]  #This is used to create a new set of vertices with a bias
                    newEdge = Part.makePolygon(tempPts)                         #Creates a new FreeCAD edge that can be used for comparison
                    #Part.show(newEdge)                                         #For debugging
                    newDist = newEdge.distToShape(edge2)[0]#np.linalg.norm(newEdge-edge2) #Finds the distance between the new and old FreeCAD edges
                    '''
                    If the passed bias is negative then an expansion occurs, so the difference between the new and old edges should be positive
                    (shown as "-bias") and the reverse for a reduction in object size. If the expansion in the x direction is incorret then
                    an attempted expnasion in the y direction occurs.
                    '''
                    if (newDist-origDist) == -bias:                             #If the difference between the edges distances is equal to the bias value
                        #This is right way to move edge
                        xVals.append(edge1First[0]+bias)                        #Create first new x vertex with the bias added
                        xVals.append(edge1Last[0]+bias)                         #Create second new x vertex with the bias added
                        if len(yVals) == 0:
                            yVals.append(0)                                     #5 vertices required to close an object, this gives the fifth vertex
                    elif (newDist-origDist) == bias:
                        #Reverse the bias value
                        xVals.append(edge1First[0]-bias)                        #Create first new x vertex with the bias subtracted
                        xVals.append(edge1Last[0]-bias)                         #Create second new x vertex with the bias subtracted
                        if len(yVals) == 0:
                            yVals.append(0)                                     #5 vertices required to close an object, this gives the fifth vertex
                    else:
                        #Add bias to the y values
                        tempPts = [FreeCAD.Vector(edge1First[0], edge1First[1]+bias, Z), \
                                    FreeCAD.Vector(edge1Last[0],edge1Last[1]+bias, Z)]
                        newEdge = Part.makePolygon(tempPts)                     #Creates a new FreeCAD edge that can be used for comparison
                        #Part.show(newEdge)                                     #For debugging
                        newDist = newEdge.distToShape(edge2)[0]#np.linalg.norm(newEdge-edge2) #Finds the distance between the new and old FreeCAD edges
                        if (newDist-origDist) == -bias:
                            #This is right way to move edge
                            yVals.append(edge1First[1]+bias)
                            yVals.append(edge1Last[1]+bias)
                            if len(xVals) == 0:
                                xVals.append(0)                                 #5 vertices required to close an object, this gives the fifth vertex
                        elif (newDist-origDist) == bias:
                            #Reverse the bias value
                            yVals.append(edge1First[1]-bias)
                            yVals.append(edge1Last[1]-bias)
                            if len(xVals) == 0:
                                xVals.append(0)                                 #5 vertices required to close an object, this gives the fifth vertex
                    break
    else:                                                                       #Object has an even number of edges greater than 4 edges
        #internalEdgeNum = 0                                                    #Not currently in use - was going to be used for edge direction counts
        '''
        Much of the following section follows the same process as above. The only difference is that there is a check to see if the edge that is being
        biased is an inside or outside edge. If it is an outside edge then the same process as above happens, and if it is an inside edge then
        there is an additional check to verify that the edge it is being compared to is an outside edge. This verifies the correct movement direction
        of the edge (in accordance with the bias) and accounts for the fact that an enlargment will require inside edges to be closer versus farther
        apart.

        See above for inline comments describing each process.
        '''
        for edge1 in feature.Edges:
            edge1First = edge1.firstVertex().Point; edge1Last = edge1.lastVertex().Point
            if (edge1First[0] == edge1Last[0] == lowX == xLow) or (edge1First[0] == edge1Last[0] == highX == xHigh):
                xVals.append(edge1First[0])
                xVals.append(edge1Last[0])
                if len(yVals) == 0:
                    yVals.append(0)                                             #5 vertices required to close an object, this gives the fifth vertex
                continue
            if (edge1First[1] == edge1Last[1] == lowY == yLow) or (edge1First[1] == edge1Last[1] == highY == yHigh):
                yVals.append(edge1First[1])
                yVals.append(edge1Last[1])
                if len(xVals) == 0:
                    xVals.append(0)                                             #5 vertices required to close an object, this gives the fifth vertex
                continue
            #print(edge1.firstVertex().Point[0], edge1.lastVertex().Point[0])   #For debugging
            edge1Dir = np.array(edge1.tangentAt(edge1.FirstParameter))#edge1.tangentAt(edge1.FirstParameter)
            for edge2 in feature.Edges:
                edge2Dir = np.array(edge2.tangentAt(edge2.FirstParameter))#edge2.tangentAt(edge2.FirstParameter)
                if (math.degrees(math.acos(np.dot(edge1Dir, edge2Dir) / (np.linalg.norm(edge1Dir)* np.linalg.norm(edge2Dir)))) == 180):
                    edge2First = edge2.firstVertex().Point; edge2Last = edge2.lastVertex().Point
                    if (edge1First[0] == lowX or edge1First[0] == highX \
                            or edge1First[1] == lowY or edge1First[1] == highY) \
                        and (edge1Last[0] == lowX or edge1Last[0] == highX \
                            or edge1Last[1] == lowY or edge1Last[1] == highY):  #If the edge is an outside edge
                        print("Edge on outside")
                        #Part.show(edge1)
                        #Part.show(edge2)
                        #print(edge1Dir)
                        #print(edge2Dir)
                        origDist = edge1.distToShape(edge2)[0]#np.linalg.norm(edge1-edge2)
                        tempPts = [FreeCAD.Vector(edge1First[0]+bias, edge1First[1], Z), \
                                    FreeCAD.Vector(edge1Last[0]+bias, edge1Last[1], Z)]
                        newEdge = Part.makePolygon(tempPts)
                        #Part.show(newEdge)
                        newDist = newEdge.distToShape(edge2)[0]#np.linalg.norm(newEdge-edge2)
                        #print(newDist, origDist)                               #For debugging
                        if (newDist-origDist) == -bias:
                            #print("Bias added to X values with a newDist of %f and origDist of %f" % (newDist, origDist))   #For debugging
                            #this is right way to move edge
                            xVals.append(edge1First[0]+bias)
                            xVals.append(edge1Last[0]+bias)
                            if len(yVals) == 0:
                                yVals.append(0)                                 #5 vertices required to close an object, this gives the fifth vertex
                        elif (newDist-origDist) == bias:
                            #print("Bias substracted from X values with a newDist of %f and origDist of %f" % (newDist, origDist))
                            #reverse the bias value
                            xVals.append(edge1First[0]-bias)
                            xVals.append(edge1Last[0]-bias)
                            if len(yVals) == 0:
                                yVals.append(0)                                 #5 vertices required to close an object, this gives the fifth vertex
                        else:
                            #add bias to the y values
                            tempPts = [FreeCAD.Vector(edge1First[0], edge1First[1]+bias, Z), \
                                        FreeCAD.Vector(edge1Last[0],edge1Last[1]+bias, Z)]
                            newEdge = Part.makePolygon(tempPts)
                            #Part.show(newEdge)
                            newDist = newEdge.distToShape(edge2)[0]#np.linalg.norm(newEdge-edge2)
                            if (newDist-origDist) == -bias:
                                #print("Bias added to Y values with a newDist of %f and origDist of %f" % (newDist, origDist))  #For debugging
                                #this is right way to move edge
                                yVals.append(edge1First[1]+bias)
                                yVals.append(edge1Last[1]+bias)
                                if len(xVals) == 0:
                                    xVals.append(0)                             #5 vertices required to close an object, this gives the fifth vertex
                            elif (newDist-origDist) == bias:
                                #print("Bias subtracted from Y values with a newDist of %f and origDist of %f" % (newDist, origDist))   #For debugging
                                #reverse the bias value
                                yVals.append(edge1First[1]-bias)
                                yVals.append(edge1Last[1]-bias)
                                if len(xVals) == 0:
                                    xVals.append(0)                             #5 vertices required to close an object, this gives the fifth vertex
                        break
                    elif ((edge2First[0] == edge2Last[0] == lowX) or (edge2First[0] == edge2Last[0] == highX) \
                            or (edge2First[1] == edge2Last[1] == lowY) or (edge2First[1] == edge2Last[1] == highY)): #This must be an inside edge (not at boundary values)
                        print("Inside edge found")
                        #Part.show(edge1)
                        #Part.show(edge2)
                        #print(edge1Dir)
                        #print(edge2Dir)
                        origDist = edge1.distToShape(edge2)[0]#np.linalg.norm(edge1-edge2)
                        tempPts = [FreeCAD.Vector(edge1First[0]+bias, edge1First[1], Z), \
                                    FreeCAD.Vector(edge1Last[0]+bias, edge1Last[1], Z)]
                        newEdge = Part.makePolygon(tempPts)
                        #Part.show(newEdge)
                        newDist = newEdge.distToShape(edge2)[0]#np.linalg.norm(newEdge-edge2)
                        if (newDist-origDist) == -bias:
                            #print("Bias added to X values with a newDist of %f and origDist of %f" % (newDist, origDist)) #For debugging
                            #this is right way to move edge
                            xVals.append(edge1First[0]+bias)
                            xVals.append(edge1Last[0]+bias)
                            if len(yVals) == 0:
                                yVals.append(0)                                 #5 vertices required to close an object, this gives the fifth vertex
                        elif (newDist-origDist) == bias:
                            #print("Bias substracted from X values with a newDist of %f and origDist of %f" % (newDist, origDist)) #For debugging
                            #reverse the bias value
                            xVals.append(edge1First[0]-bias)
                            xVals.append(edge1Last[0]-bias)
                            if len(yVals) == 0:
                                yVals.append(0)                                 #5 vertices required to close an object, this gives the fifth vertex
                        else:
                            #add bias to the y values
                            tempPts = [FreeCAD.Vector(edge1First[0], edge1First[1]+bias, Z), \
                                        FreeCAD.Vector(edge1Last[0],edge1Last[1]+bias, Z)]
                            newEdge = Part.makePolygon(tempPts)
                            #Part.show(newEdge)
                            newDist = newEdge.distToShape(edge2)[0]#np.linalg.norm(newEdge-edge2)
                            if (newDist-origDist) == -bias:
                                #print("Bias added to Y values with a newDist of %f and origDist of %f" % (newDist, origDist)) #For debugging
                                #this is right way to move edge
                                yVals.append(edge1First[1]+bias)
                                yVals.append(edge1Last[1]+bias)
                                if len(xVals) == 0:
                                    xVals.append(0)                             #5 vertices required to close an object, this gives the fifth vertex
                            elif (newDist-origDist) == bias:
                                #print("Bias subtracted from Y values with a newDist of %f and origDist of %f" % (newDist, origDist)) #For debugging
                                #reverse the bias value
                                yVals.append(edge1First[1]-bias)
                                yVals.append(edge1Last[1]-bias)
                                if len(xVals) == 0:
                                    xVals.append(0)                             #5 vertices required to close an object, this gives the fifth vertex
                        break
    if xVals[0] == 0:                                                           #Corrects the 5th vertex so that the shape is properly closed
        xVals[0] = xVals[-1]
        yVals.append(yVals[0])
    elif yVals[0] == 0:                                                         #Corrects the 5th vertex so that the shape is properly closed
        yVals[0] = yVals[-1]
        xVals.append(xVals[0])
    #print(len(xVals),len(yVals))                                               #For debugging
    #print(xVals)
    #print(yVals)
    finalVerts = []                                                             #New array to hold a tuple of the final vertices
    for idx in range(0,len(xVals)):                                             #The length of xVals and yVals are equal, this loop runs through them to create new vertices
        if idx == 0:                                                            #If this is the first vertex, find the highest value from the ends of the arrays
            #Solve for first and last vertex
            if abs(xVals[0]) > abs(xVals[-1]):                                  #Determines the x value for the first vertex
                xFin = xVals[0]
            else:
                xFin = xVals[-1]
            if abs(yVals[0]) > abs(yVals[-1]):                                  #Determines the y value for the first vertex
                yFin = yVals[0]
            else:
                yFin = yVals[-1]
            finalVerts.append((xFin,yFin,Z))
        elif idx == len(xVals)-1:                                               #Sets the last vertex equal to the first vertex so the object is closed
            #set equal to first point
            finalVerts.append(finalVerts[0])
        else:
            finalVerts.append((xVals[idx],yVals[idx],Z))
    #print(len(finalVerts))
    #print(finalVerts)                                                          #For debugging
    pts=[]
    for i in range(0,len(finalVerts)):                                          #Used to create an array of the "Vector points" required in FreeCAD
        pts.append(FreeCAD.Vector(finalVerts[i][0],finalVerts[i][1],finalVerts[i][2])) #FreeCAD.Vector(x,y,z)
    #print(pts)
    wire=Part.makePolygon(pts)                                                  #Connects all points given above, makes a wire polygon (just a connected line)
    #Part.show(wire)
    face=Part.Face(wire)                                                        #Creates a face from the wire above
    print("Bias end")
    return face                                                                 #Returns the new face that has been biased

import xml.etree.ElementTree as ET                                              #Required to read the lyp (layer properties) file
import itertools                                                                #Used for iterating in the parsers
import operator                                                                 #Used for parsing
import re                                                                       #Regex, used for sorting and parsing
import sys, importlib                                                           #Used for importing and reloading modules
try:                                                                            #Only runs reload if it is needed (not needed on first run through)
    importlib.reload(sys.modules['supporting_functions'])                    #Reloads any changes in modules
except:
    print("Reload not needed for supporting_functions")
import supporting_functions as sp

def extract_gds2_info(filepath):                                                #Extracts information from the gds2 file, requires .txt format
    print("extract_gds2_info Start")                                            #For debugging
    with open(filepath) as myfile:                                              #Opens  and closes the file from gds2Filepath
        content = myfile.read()                                                 #Reads file as one string instead of individual lines
    with open(filepath) as myfile:                                              #Opens and closes file from gds2 Filepath
        text = myfile.readlines()                                               #Reads all lines, line by line
    layer=[]                                                                    #Set up empty array for layer names
    layer_loc=[]                                                                #Empty layer index array
    all_polygons = []                                                           #Keeps track of all polygons
    for line in text:                                                           #Extracts layer names from the text.
        if "LAYER" in line:                                                     #Finds each line with Layer and seperates it to get all layer names
            #print(line)                                                        #For debugging
            lineholder = line.replace(" ","")                                   #Replaces all spaces with nothing (deletes spaces)
            lineholder = lineholder.rstrip()                                    #Deletes leading and following whitespace characters (tab, new line, etc)
            layer_loc.append(lineholder.lower())                                #Converts "LAYER" to "layer"
    temp = content.split("BOUNDARY")                                            #Splits off the content at "BOUNDARY"
    for idx,i in enumerate(temp[1:]):                                           #Enumerate pulls a counter (idx) and whats at each index (i)
        xygroups = re.search(r'XY.*?ENDEL', i, re.DOTALL).group()               #Sections off material between XY and ENDEL and groups it
        xypoints = xygroups.split("XY")[1].split("ENDEL")[0].split("\n")        #Removes the XY and ENDEL and splits each line into an element
        xypoints.pop()                                                          #Removes the last element which is '' - not sure why it appears
        xynowhite = []                                                          #Array used to remove white space
        x = []; y = []                                                          #x and y point arrays
        xyfinal = []                                                            #Array for final xy points after they are split
        for first in xypoints:                                                  #Loop to delete spaces
            xynowhite.append(first.replace(" ",""))
        for z in xynowhite:                                                     #Loop to split the X:Y coords into X and Y tuples in xyfinal array
            xyfinal.append(z.split(":"))
        for inside in xyfinal:                                                  #Seperates the x and y from each tuple in xyfinal array
            x.append(int(inside[0]))
            y.append(int(inside[1]))
        all_polygons.append(sp.Polygon(x,y,layer_loc[idx]))                     #Creates new polygon class and attaches it to the list
    get_attr = operator.attrgetter('ids')                                       #Seperates by ids attribute inside poylgon class
    '''
    Below line creates a list of polygon classes sorting them by their ids
    Sorted_polygons is a list of lists where first index is the sorted group (layer #) and second index is each class within that group
    layer1, layer12, layer2 as examples
    '''
    sorted_polygons = [list(g) for k, g in itertools.groupby(sorted(all_polygons, key=get_attr), get_attr)]
    '''
    Below dictionary is creating a dictionary of polygons where the key is the ids (layer number) and the elements are
    added as the information held by that key. So calling layer1 key returns all features existing in layer1
    '''
    finaldict = {sorted_polygons[0][0].ids : sorted_polygons[0][:]}
    for idx, i in enumerate(sorted_polygons[1:]):
        tempdict = {sorted_polygons[idx+1][0].ids : sorted_polygons[idx+1][:]}  #Creates a temporary dictionary so the whole one can be updated
        finaldict.update(tempdict)                                              #This .update is similar to .append for lists, where it creates a new element at the end
    print("extract_gds2_info End")                                              #For debugging
    return finaldict

def get_lyp_data(filename):                                                     #Extracts information from the layer properties file, requires .lyp format
    print("get_lyp_data Start")                                                 #For debugging
    tree = ET.parse(filename)                                                   #Sets up parser for passed filename
    root = tree.getroot()                                                       #Finds the begining of the file
    for indx,el in enumerate(root[0]):                                          #Find index locations for our desired elements of the .lyp file
        #print(el.tag,indx)
        if el.tag == "name":                                                    #Adds key for name
            n_indx = int(indx)
        if el.tag == "source":                                                  #Adds key for source
            source_indx = int(indx)
        if el.tag == "fill-color":                                              #Adds key for color
            c_indx = int(indx)

    name_dict = {}
    for child in enumerate(root[:-1]):                                          #Extract information for dictionary. Last index is name for some reason?
        ln = "layer"+child[1][source_indx].text.split("/")[0]                   #Splits on the / and takes the left side (first element)
        name = child[1][n_indx].text                                            #Extracts the names
        color = child[1][c_indx].text                                           #Extracts the colors
        try:                                                                    #Try and add to the dictionary by reference key
            name_dict[ln].append([name,color])
        except KeyError:                                                        #If reference doesn't exist append new index to currently existing items
            name_dict = {**name_dict, **{ln: [name,color]}}
    print("get_lyp_data End")                                                   #For debugging
    return name_dict

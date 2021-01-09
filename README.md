# Overview
3D_GDS2Converter was designed for the conversion of 2D KLayout/GDS2 models to 3D FreeCAD/STEP models using XSection scripts (.xs). 


## Requirements 
3D_GDS2Converter was built on FreeCAD 0.19+; however, it should work with FreeCAD 0.18+ as well. Additionally 2 input files are required - a GDS2 text file (*.txt) and a XSection script (*.xs). A layer properties file is optional, but can define colors for layers (otherwise colors are automatically assigned). 


## Setup and Usage Instructions
3D_GDS2Converter is currently setup to use as a FreeCAD Macro. 

To run the program download or clone the repository files to any local location. 
Open FreeCAD and go to Macro -> Macros... then select Create and choose a name with the Python extension (.py). 

[macroGIF]

The new macro will automatically open in edit mode. Copy over the contents of the main_PvX.py file into the extension. From here the macro can be run (ctrl+F6) and then the file 
location of the other python modules can be selected. 
Once the location of the supporting modules has been selected a menu for selecting the input files will appear in which the GDS2 (.txt) and the cross section script (.xs) are required; however, the layer properties (.lyp) file is optional and can be used for coloring the layers (unique layer names matching the layer names in the cross section script are required). 

_Note: The program is currently designed on a .001 micron scale. To use a different scale go to the supporting_functions_PvX script and change the division value (from 10) to the desired value (relative to thickness) inside the get_xy_points function._
INSERT PICTURES OF ABOVE

The code has the option to export all final objects as STEP files, each object will be it's own STEP file so that they can be imported and viewed as individual layers. When
running the program a message will pop up requesting if the objects should be exported - click Affirmative and select the output folder and they will be exported to that folder.


# Current Features
3D_GDS2Converter was designed to work directly with the XSection tool for KLayout (see [XSection DocReference] for more details). As such, the functionality of the code is based around the functions included in the XSection tool (names are not the same). Because XSection scripts are written in Ruby, they are not directly evaluted and instead are read line by line extracting the commands in Python.

_Note: all function calls and standard options used in the XSection tool inside KLayout must be included. I.e. using '.inverted' creates standard features and not including '.inverted' results in vias/holes being created._

**Currently implemented functions:**  INCLUDE PICTURES
### bulk
Uses an outline layer to create a substrate (auto-detects largest object to use as outline/substrate layer)

### deposit
deposit is used in 2 different ways inside of the XSection tool
1. As a base deposition to create features out of
2. As a blanket deposition to cover the entire substrate (including all features)

3D_GDS2Converter ignores the first usage and instead creates all features individually (see etch below); however, 3D_GDS2Converter was written to take the .xs file directly from being used in KLayout so the deposit functions calls should all remain and the deposit for features should be ignored leaving only the blanket depositions. The blanket deposition will use the same outline layer used in bulk to ensure that the entire surface is covered (passing another layer will have no effect). 

### etch
The etch command creates features based off the designated layer. The following options of the etch command have been implemented:
1. taper: this chamfers the outside edges of all the features on this layer (valid for 10 degrees to 80 degrees). 
2. bias: A positive bias will increase the length of all sides by twice the amount given. A negative bias will decrease the length of all sides by twice the amount given.
The following functions might be implemented at a future date:

1. mode: allows for curved-based objects that could require a fillet instead of a chamfer 
2. burried: allows for a shift up or down of all features

The following functions have no affect in this code and will not be imlemented (they can be in the .xs file, but they are ignored):
1. into
2. through

For more information see the [etch method]

### layer
This function finds and returns the layer names. These names are used to name the final displayed objects, as well as to access colors from the layer properties file.

### planarize
This function creates a planarized layer on top of all the other layers, at a set height. The height of this planarized layer is only adjustable inside the code (Planarize_PvX file). Currently, no specific options have been created for this function - any included options will be ignored and a simple planarized layer will be created on top.


#### Limitations 
- 3D_GDS2Converter is designed for work for a single layout and may not work properly for multiple different layouts that are not intersecting each other. 
- Some functions of the cross section tool for KLayout have not been implemented (some have no plans to be added at this time). 
- Curved objects are currently not accepted as no function to properly chamfer them has been introduced, this is planned for a future version.
- Biasing of objects may not work completely for complex objects. 
- Fillet has not been implemented (only straight chamfers)

#### Coming Soon
- FreeCAD AddOn support.
- Version control and better Git access.
- Improved runtime, optimization, and better storage management (should improve RAM usage significantly). 
- Additional functionality, such as curved object support and other complex object support. 


# License 
3D_GDS2Converter is free software: you can redistribute it and/or modify it under the terms of the GNU LGPL as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

3D_GDS2Converter is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU LGPL for more details.


### Warnings
- Due to the complexity of this program, and the current lack of optimization, the program can take upwards of 60 minutes to run for non-simple layouts. 
- This program is not complete and as such there might be errors that occur; most of these errors will be given by FreeCAD and will pertain to an imporper usage of FreeCAD functions inside this program or invalid inputs to this program causing invalid objects inside FreeCAD.
- This program is RAM intensive, for complex layouts it has been seen spiking at nearly 10 GB of RAM, as such at least 16 GB of RAM is recommended. 



[XSection DocReference]: https://sourceforge.net/p/xsectionklayout/wiki/DocReference/#xs-file-reference
[etch method]: https://sourceforge.net/p/xsectionklayout/wiki/DocEtch/
[macroGIF]: https://github.com/Amorphyx/3D_GDS2Converter/blob/main/Images/macro2.gif

#!/usr/bin/python
# -*- coding: utf-8 -*-
#########################################################
# Automated Alignment and data preparation for FIB/SEM 
# image stacks
#
# © 2020 Florian Kleiner
#   Bauhaus-Universität Weimar
#   Finger-Institut für Baustoffkunde
#
# programmed using python 3.7,
# Fiji/ImageJ 1.52k
#
#########################################################


import csv
import os, sys, getopt
import re
import subprocess
import math
import tkinter as tk
import mmap
import shutil
import xml.etree.ElementTree as ET
import statistics
from tkinter import filedialog
from subprocess import check_output

# check for dependencies
home_dir = os.path.dirname(os.path.realpath(__file__))
# import image_recombination script
ir_path = os.path.dirname( home_dir ) + '/image_recombination/'
ir_file = 'image_recombination'
if ( os.path.isfile( ir_path + ir_file + '.py' ) or os.path.isfile( home_dir + ir_file + '.py' ) ):
    if ( os.path.isdir( ir_path ) ): sys.path.insert( 1, ir_path )
    import image_recombination as ir
else:
    programInfo()
    print( 'missing ' + ir_path + 'image_recombination.py!' )
    print( 'download from https://github.com/kleinerELM/image_recobination' )
    sys.exit()

def programInfo():
    print("#########################################################")
    print("# Automatic stitching of Images from a Maps Project     #")
    print("#                                                       #")
    print("# © 2019 Florian Kleiner                                #")
    print("#   Bauhaus-Universität Weimar                          #")
    print("#   Finger-Institut für Baustoffkunde                   #")
    print("#                                                       #")
    print("#########################################################")
    print()

def processArguments():
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-i] [-c] [-d]"
    try:
        opts, args = getopt.getopt(argv,"himfcd",["noImageJ="])
        for opt, arg in opts:
            if opt == '-h':
                print( 'usage: ' + usage )
                print( '-h,                  : show this help' )
                print( '-i, --noImageJ       : skip ImageJ processing' )
                print( '-c                   : disable curtaining removal' )
                print( '-f                   : set a scale factor of the resulting images' )
                print( '-d                   : show debug output' )
                print( '' )
                sys.exit()
            elif opt in ("-i", "-noImageJ"):
                print( 'deactivating ImageJ processing!' )
                global runImageJ_Script
                runImageJ_Script = False
            elif opt in ("-c"):
                print( 'curtaining removal deactivatd!' )
                global removeCurtaining
                removeCurtaining = 0
            elif opt in ("-d"):
                print( 'show debugging output' )
                global showDebuggingOutput
                showDebuggingOutput = True
            elif opt in ("-f"):
                if ( int( arg ) <= 1 and int( arg ) > 0 ):
                    global forcedScaleFactor
                    forcedScaleFactor = float( arg )
                    print( 'set scale factor to ' + str( forcedScaleFactor ) )
                showDebuggingOutput = True
    except getopt.GetoptError:
        print( usage )
    print( '' )

""" def combineImagesImageJ( directory, outputDirectory, title, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber ):
    imageSize = int(width) * int(height) * forcedScaleFactor * forcedScaleFactor
    if ( imageSize < 2000000000 ):
        scaleFactor = forcedScaleFactor
    else:
        humanReadableImageSize = round( imageSize / 1000000000, 2)
        print( "  image is exceeding 2 Gigapixel (" + str( humanReadableImageSize ) + " GP) and therefore too large for ImageJ" )
        scaleFactor = 0.5*forcedScaleFactor
        humanReadableImageSize = round( imageSize*scaleFactor*scaleFactor / 1000000000, 2)
        scaleX_old = scaleX
        scaleX = scaleX/scaleFactor
        scaleY = scaleY/scaleFactor
        print( "    - scaling with factor " + str( scaleFactor ) + " to " + str( humanReadableImageSize ) + " GP)" )
        print( "    - changed scale from " + str( scaleX_old ) + " to " + str( scaleX ) + " nm per Pixel!" )
    
    command = "ImageJ-win64.exe -macro \"" + home_dir +"\easyCombine.ijm\" \"" + directory + "/|" + outputDirectory + "/|" + str( scaleX ) + "|" + str( scaleY ) + "|" + str( width ) + "|" + str( height ) + "|" + str(gridWidth) + "|" + str(gridHeight) + "|" + title + "|" + str(layerNumber)+ "|" + str(scaleFactor) + "\""

    print( "  starting ImageJ Macro..." )
    if ( showDebuggingOutput ) : print( '  ' + command )
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print( "  Error" )#"returned error (code {}): {}".format(e.returncode, e.output))
        pass """

def getFileList( directory, HDView_dir, gridWidth, gridHeight, layerNumber ):
    allowed_file_extensions = [ '.tif', '.png' ]
    tile_count = 0
    workingDirectory = directory + '/' + HDView_dir + '/data/'
    fileNameList = []
    if os.path.isdir( workingDirectory ) :
        for i in range( gridWidth ):
            path = workingDirectory + "l_" + str( int(layerNumber)-1 ) + "/c_" + str( i ) + "/"
            for j in range( gridHeight ):
                filePath = path + "tile_" + str( j ) +".tif"
                if ( os.path.isfile( filePath ) ):
                    fileNameList.append( filePath )
                else:
                    print( "  ERROR: expected file is missing: '" + filePath + "'"  )
    else:
        print( "  Error: '" + workingDirectory + "' is no directory")

    return fileNameList

def combineImagesPython( directory, outputDirectory, HDView_dir, title, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber ):
    imageSize = int(width) * int(height) * forcedScaleFactor * forcedScaleFactor
    if ( imageSize < 2000000000 ):
        scaleFactor = forcedScaleFactor
    else:
        humanReadableImageSize = round( imageSize / 1000000000, 2)
        print( "  image is exceeding 2 Gigapixel (" + str( humanReadableImageSize ) + " GP) and therefore too large for ImageJ" )
        scaleFactor = 0.5*forcedScaleFactor
        humanReadableImageSize = round( imageSize*scaleFactor*scaleFactor / 1000000000, 2)
        scaleX_old = scaleX
        scaleX = scaleX/scaleFactor
        scaleY = scaleY/scaleFactor
        print( "    - scaling with factor " + str( scaleFactor ) + " to " + str( humanReadableImageSize ) + " GP)" )
        print( "    - changed scale from " + str( scaleX_old ) + " to " + str( scaleX ) + " nm per Pixel!" )
    
    ir_settings = ir.getBaseSettings()
    ir_settings["workingDirectory"] = directory #+ "/LayersData/Layer/"
    ir_settings["outputDirectory"] = outputDirectory #+ "/LayersData/Layer/"
    ir_settings["fileType"] = ".tif"
    ir_settings["col_count"] = gridWidth
    ir_settings["row_count"] = gridHeight
    ir_settings["scaleX"] = scaleX
    ir_settings["scaleY"] = scaleY
    ir_settings["scaleUnit"] = 'nm'
    ir_settings["scaleFactor"] = scaleFactor
    ir_settings["tile_count"] = ( gridWidth * gridHeight )
    ir_settings["imageDirection"] = 'v' # vertical direction
    ir_settings["createThumbnail"] = True
    ir_settings["showDebuggingOutput"] = True
    fileNameList = getFileList( directory, HDView_dir, gridWidth, gridHeight, layerNumber )
    ir.stitchImages( ir_settings, fileNameList )

def cmdExists(cmd):
    return shutil.which(cmd) is not None

def imageJInPATH():
    if ( not cmdExists( "ImageJ-win64.exe" ) ):
        if os.name == 'nt':
            print( "make sure you have Fiji/ImageJ installed and added the program path to the PATH variable" )
            command = "rundll32 sysdm.cpl,EditEnvironmentVariables"
            try:
                subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                print( "Error" )#"returned error (code {}): {}".format(e.returncode, e.output))
                pass
            print( "make sure you have Fiji/ImageJ installed and added the program path to the PATH variable" )
        else:
            print( "make sure Fiji/ImageJ is accessible from command line" )
        return False
    elif ( showDebuggingOutput ) : print( "Fiji/ImageJ found!" )
    return True

def readProjectData( directory ):    
    projectDataXML = directory + "\MapsProject.xml"
    if ( not os.path.isfile( projectDataXML ) ):
        projectDataXML = filedialog.askopenfilename(title='Please select MapsProject.xml')
        projectDir = os.path.abspath(os.path.join(projectDataXML, os.pardir))

    tree = ET.ElementTree(file=projectDataXML)
    root = tree.getroot()
    XMLnamespace = re.search('{(.*)}', root.tag).group(1)

    description = root.find('{' + XMLnamespace + '}description ')
    projectName = ''
    projectDescription = ''
    layerNames = []
    layerFolders = []
    for element in root:
        if ( element.tag == '{' + XMLnamespace + '}displayName' ):
            projectName = element.text
        if ( element.tag == '{' + XMLnamespace + '}description' ):
            projectDescription = element.text
    if ( projectName != '' ):
        print( 'Projektname:         ' + projectName )
        if projectDescription is None: projectDescription = ''
        print( 'Projektbeschreibung: ' + projectDescription )
        print(  )
        #layers = root.find('{' + XMLnamespace + '}LayerGroups/{' + XMLnamespace + '}LayerGroup/{' + XMLnamespace + '}Layers')
        #layerGroup = root.find('{' + XMLnamespace + '}LayerGroups/{' + XMLnamespace + '}LayerGroup')
        layerGroups = root.find('{' + XMLnamespace + '}LayerGroups')
        for layerGroup in layerGroups:
            if ( layerGroup.tag == '{' + XMLnamespace + '}LayerGroup' ):
                for layers in layerGroup:
                    if ( layers.tag == '{' + XMLnamespace + '}Layers' ):
                        for element in layers:
                            #print( str(element.tag) )
                            for layer in element:
                                if ( layer.tag == '{' + XMLnamespace + '}displayName' ):
                                    #print( ' - displayName : ' + str(layer.text) )
                                    layerFolders.append( layer.text )
                                if ( layer.tag == '{' + XMLnamespace + '}RealDisplayName' ):
                                    #print( ' - RealDisplayName : ' + str(layer.text) )
                                    layerNames.append( layer.text )
                                    
        i = 0
        while i < len(layerNames):
            print( 'opening layer "' + str(layerNames[i]) + '"' )
            title = str(layerNames[i])
            
            HDView_dir = '0' # directory in which the HDView files (pyramid.xml and tile images) are stored.
            layer_dir = directory + '/'  + layerFolders[i] + '/' 
            for subdir in os.listdir( layer_dir ):
                if ( os.path.isdir( layer_dir + subdir ) ):
                    HDView_dir = subdir

            pyramid_path = layer_dir + HDView_dir + '/data/pyramid.xml'
            if os.path.isfile( pyramid_path ):
                print( ' found stitched layer!' )
                layerTree = ET.ElementTree(file=pyramid_path)
                layerRoot = layerTree.getroot()
                isNavCam = True
                for element in layerRoot:
                    #print( '  -' + element.tag )
                    if ( element.tag == 'imageset' ):
                        #print( '  ' + element.attrib['url'] )
                        layerNumber = element.attrib['levels']
                        width = element.attrib['width']
                        height = element.attrib['height']
                        gridWidth = round( int( element.attrib['width'] ) / int( element.attrib['tileWidth'] ) )
                        gridHeight = round( int( element.attrib['height'] ) / int( element.attrib['tileHeight'] ) )
                        print( '  layer count: ' + layerNumber )
                        print( '  image size: ' + width + ' x ' + height + ' px (Grid: '+ str( gridWidth ) + " x " + str( gridHeight ) + ")" )
                    for subelement in element:
                        if ( subelement.tag == 'pixelsize' ):
                            isNavCam = False
                            for subsubelement in subelement:
                                if ( subsubelement.tag == 'x' ):
                                    scaleX = float( subsubelement.text )*1000000000
                                if ( subsubelement.tag == 'y' ):
                                    scaleY = float( subsubelement.text )*1000000000
                            print('  Scale : ' + str(scaleX) + " nm per pixel" )
                            combineImagesPython( directory + "/" + layerFolders[i].replace('\\', '/'), directory, HDView_dir, title, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber )
                            #if ( runImageJ_Script and imageJInPATH() ):
                            #    combineImagesImageJ( directory + "/" + layerFolders[i].replace('\\', '/'), directory, title, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber )
                            #else:
                            #    if ( showDebuggingOutput ) : print( "...doing nothing!" )
                if ( isNavCam ):
                    if ( runImageJ_Script and imageJInPATH() ):
                        print( "  probably a NavCam Image!" )
                        #estimated scale: 2 cm for 468 px
                        scaleX = scaleY = 42735 # 20 000 000 nm / 468 px
                        print('  Estimated scale as: ' + str(scaleX) + " nm per pixel" )
                        #combineImagesImageJ( directory + "/" + layerFolders[i].replace('\\', '/'), directory, title, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber )
                        combineImagesPython( directory + "/" + layerFolders[i].replace('\\', '/'), directory, HDView_dir, title, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber )
                    else:
                        if ( showDebuggingOutput ) : print( "...doing nothing!" )
            else:
                print( ' found unstitched Tile Set' )
                if ( showDebuggingOutput ) : print( ' Searched for pyramid.xml in: "' + pyramid_path )
                if ( showDebuggingOutput ) : print( ' no algorithm implemented yet, aborting...')
            print()
            i=i+1
    else:
        print( 'kein Projekt gefunden!' )

### actual program start
if __name__ == '__main__':
    #### global var definitions
    root = tk.Tk()
    root.withdraw()

    voxelSizeX = 0
    voxelSizeY = 0
    resX = 0
    resY = 0

    runImageJ_Script = True #False
    removeCurtaining = 1
    createLogVideos = "n"
    showDebuggingOutput = False
    outputType = 0 # standard output type (y-axis value) is area-%
    thresholdLimit = 140
    infoBarHeight = 0
    metricScale = 0
    pixelScale  = 0
    startFrame = 0
    endFrame = 0
    forcedScaleFactor = 1

    ### global settings    
    programInfo()
    processArguments()
    if ( showDebuggingOutput ) : print( "I am living in '" + home_dir + "'" )

    workingDirectory = filedialog.askdirectory(title='Please select the image / working directory')

    if ( workingDirectory != "" ) :
        print( "Selected working directory: " + workingDirectory )
        readProjectData( workingDirectory )
        
    else:
        print("No directory selected")


    print("-------")
    print("DONE!")

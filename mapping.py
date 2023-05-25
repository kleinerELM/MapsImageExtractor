#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, getopt, shutil
import re
import subprocess
import math
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog
from subprocess import check_output

def programInfo():
    print("#########################################################")
    print("# Automatic stitching of Images from a Maps Project     #")
    print("#                                                       #")
    print("# © 2023 Florian Kleiner                                #")
    print("#   Bauhaus-Universität Weimar                          #")
    print("#   Finger-Institut für Baustoffkunde                   #")
    print("#                                                       #")
    print("#########################################################")
    print()

# check for dependencies
home_dir = os.path.dirname(os.path.realpath(__file__))
# import image_recombination script
ir_name = 'image_recombination'
ir_path = os.path.dirname( home_dir ) + os.sep + ir_name + os.sep
if ( os.path.isfile( ir_path + ir_name + '.py' ) or os.path.isfile( home_dir + ir_name + '.py' ) ):
    if ( os.path.isdir( ir_path ) ): sys.path.insert( 1, ir_path )
    import image_recombination as ir
else:
    programInfo()
    print( 'missing ' + ir_path + ir_name +'.py!' )
    print( 'download from https://github.com/kleinerELM/image_recobination' )
    sys.exit()

def processArguments():
    global imageSizeLimit
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-i] [-c] [-s] [-l:] [-d]"
    try:
        opts, args = getopt.getopt(argv,"himfcsl:d",["noImageJ="])
        for opt, arg in opts:
            if opt == '-h':
                print( 'usage: ' + usage )
                print( '-h,                  : show this help' )
                print( '-i, --noImageJ       : skip ImageJ processing' )
                print( '-c                   : disable curtaining removal' )
                print( '-f                   : set a scale factor of the resulting images' )
                print( '-s                   : manually stitch a single dataset from a "(stitched)" folder' )
                print( '-l                   : Limit the image size to {} Gigapixel'.format(imageSizeLimit) )
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
            elif opt in ("-s"):
                print( 'manually stitch a single dataset from a "(stitched)" folder' )
                global singleDataSet
                singleDataSet = True
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

def getFileList( directory, HDView_dir, gridWidth, gridHeight, layerNumber ):
    workingDirectory = directory + os.sep + HDView_dir + os.sep + 'data' + os.sep + "l_{}".format(int(layerNumber)-1)
    fileNameList = []
    fileNameListEmpty = []
    if os.path.isdir( workingDirectory ) :
        for i in range( gridWidth ):
            path = workingDirectory  + os.sep + "c_{}".format(i) + os.sep
            for j in range( gridHeight ):
                filePath = path + "tile_{}.tif".format(j)
                if ( os.path.isfile( filePath ) ):
                    fileNameList.append( filePath )
                else:
                    fileNameList.append( 'EMPTY' )
                    fileNameListEmpty.append("tile_{}.tif".format(j))
    else:
        print( "  Error: '" + workingDirectory + "' is no directory")

    if len(fileNameListEmpty) > 0:
        print('   Warning: missing {} files:'.format(len(fileNameListEmpty)))
        for i, filename in enumerate( fileNameListEmpty ):
            if i < 3: print('   - {}'.format(filename))
            else:
                print('   - ...')
                break

    return fileNameList

def combineImagesPython( directory, outputDirectory, HDView_dir,  width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber, result_file_name ):
    global forcedScaleFactor
    imageSize = int(width) * int(height) * (forcedScaleFactor**2)
    imageSizeLimitPx = imageSizeLimit*(10**9)
    if imageSize > imageSizeLimitPx:
        forcedScaleFactor = round(math.sqrt(imageSizeLimitPx / imageSize), 3)
        imageSize = int(width) * int(height) * (forcedScaleFactor**2)
        print( "\n  changed scale factor to {}".format( forcedScaleFactor ) )
    if ( imageSize < imageSizeLimitPx ):
        scaleFactor = forcedScaleFactor
    else:
        print( "  image is exceeding {} Gigapixel ({:.2f} GP) and therefore is too large for ImageJ".format(imageSizeLimit, imageSize / (10**9)) )
        scaleFactor = 0.5*forcedScaleFactor
        scaleX_old = scaleX
        scaleX = scaleX/scaleFactor
        scaleY = scaleY/scaleFactor
        print( "    - scaling with factor {:.2f} to {:.2f} GP".format(scaleFactor, imageSize*scaleFactor*scaleFactor / (10**9) ) )
        print( "    - changed scale from {:.2f} to {:.2f} nm per Pixel!".format(scaleX_old, scaleX) )
    fileNameList = getFileList( directory, HDView_dir, gridWidth, gridHeight, layerNumber )

    if fileNameList != []:
        ir_settings = ir.getBaseSettings()
        ir_settings["workingDirectory"] = workingDirectory #+ "/LayersData/Layer/"
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
        ir_settings["showDebuggingOutput"] = showDebuggingOutput
        ir_settings["cropX"] = int(int(width)*scaleFactor)
        ir_settings["cropY"] = int(int(height)*scaleFactor)

        ir.stitchImages( ir_settings, fileNameList, result_file_name = result_file_name )

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
    projectDataXML = directory + os.sep + "MapsProject.xml"
    if ( not os.path.isfile( projectDataXML ) ):
        projectDataXML = filedialog.askopenfilename(title='Please select MapsProject.xml')
        projectDir = os.path.abspath(os.path.join(projectDataXML, os.pardir))

    tree = ET.ElementTree(file=projectDataXML)
    root = tree.getroot()
    XMLnamespace = re.search('{(.*)}', root.tag).group(1)

    projectName = ''
    projectDescription = ''
    layerNames = []
    layerFolders = []
    layerFileName = []
    for element in root:
        if ( element.tag == '{' + XMLnamespace + '}displayName' ):
            projectName = element.text
        if ( element.tag == '{' + XMLnamespace + '}description' ):
            projectDescription = element.text
    if ( projectName != '' ):
        print( "Projektname:         {}".format(projectName) )
        if projectDescription is None: projectDescription = ''
        print( "Projektbeschreibung: {}\n".format(projectDescription) )

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
                                    layerNames.append( layer.text.split('\\')[2] )
                                    layerFileName.append( layer.text.split('\\')[1] + '-' + layer.text.split('\\')[2] )
                                    layerFolders.append( layer.text )
                                #if ( layer.tag == '{' + XMLnamespace + '}RealDisplayName' ):
                                #    print( ' - RealDisplayName : ' + str(layer.text) )
                                #    layerNames.append( layer.text )

        i = 0
        while i < len(layerNames):
            print( 'opening layer "{}"'.format(layerFileName[i]) )
            title = str(layerNames[i])

            HDView_dir = '0' # directory in which the HDView files (pyramid.xml and tile images) are stored.
            layer_dir = directory + os.sep + layerFolders[i] + os.sep
            if os.path.isdir( layer_dir ):
                for subdir in os.listdir( layer_dir ):
                    if subdir != 'histograms':
                        if ( os.path.isdir( layer_dir + subdir ) ):
                            HDView_dir = subdir

                pyramid_path = layer_dir + HDView_dir + os.sep + "data" + os.sep + "pyramid.xml"
                if os.path.isfile( pyramid_path ):
                    print( ' found stitched layer!' )
                    layerTree = ET.ElementTree(file=pyramid_path)
                    layerRoot = layerTree.getroot()
                    isNavCam = True
                    for element in layerRoot:
                        if ( element.tag == 'imageset' ):
                            layerNumber = element.attrib['levels']
                            width  = int( element.attrib['width'] )
                            height = int( element.attrib['height'] )
                            gridWidth  = round( width  / int( element.attrib['tileWidth'] ) )
                            gridHeight = round( height / int( element.attrib['tileHeight'] ) )
                            print( "  layer count: {}".format(layerNumber) )
                            print( "  image size : {} x {} px (Grid: {} x {})".format(width, height, gridWidth, gridHeight) )
                        for subelement in element:
                            if ( subelement.tag == 'pixelsize' ):
                                isNavCam = False
                                for subsubelement in subelement:
                                    if ( subsubelement.tag == 'x' ):
                                        scaleX = float( subsubelement.text )*10**9
                                    if ( subsubelement.tag == 'y' ):
                                        scaleY = float( subsubelement.text )*10**9
                                print('  Scale      : ' + str(scaleX) + " nm per pixel" )
                                break

                    if ( isNavCam ):
                        print( "  probably a NavCam Image!" )
                        #estimated scale: 25 mm for 470 px
                        scaleX = scaleY = 53191 # 25 000 000 nm / 470 px
                        print("  Estimated scale as: {} nm per pixel".format(scaleX) )

                    combineImagesPython( directory + os.sep + layerFolders[i].replace('\\', os.sep), directory, HDView_dir, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber, layerFileName[i] )
                else:
                    print( ' found unstitched Tile Set' )
                    if showDebuggingOutput: print( ' Searched for pyramid.xml in: "{}"'.format(pyramid_path) )
                    if showDebuggingOutput: print( ' no algorithm implemented yet, aborting...')
                    elements = [f for f in os.listdir(layer_dir) if os.path.isfile(os.path.join(layer_dir, f))]
                    elements = sorted(elements)
                    last_element = elements[-1]
                    print("  found {} files".format(len(elements)))
                    if len(elements) > 1:
                        pos_string = last_element.split('_')
                        grid_def = pos_string[1].split('-')

                        gridWidth = int(grid_def[0])
                        gridHeight = int(grid_def[1])

                        combineImagesPython( directory + os.sep + layerFolders[i].replace('\\', os.sep), directory, HDView_dir, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber, layerFileName[i] )
                    else:
                        print( os.path.join(layer_dir, last_element) )
                        target = directory + os.sep + elements[0]
                        shutil.copy(os.path.join(layer_dir, last_element), target)

            else:
                if ( showDebuggingOutput ) : print( ' folder "' + layer_dir + '" not found')
            print()
            i += 1
    else:
        print( 'kein Projekt gefunden!' )

def readSingleDataSet(workingDirectory):
    layer_dir = os.path.dirname(workingDirectory) + os.sep
    HDView_dir = os.path.basename(workingDirectory)
    title = str(os.path.basename(os.path.dirname(workingDirectory)))

    print(layer_dir, '|HDView_dir:', HDView_dir, '|title:', title)
    pyramid_path = layer_dir + HDView_dir + os.sep + "data" + os.sep + "pyramid.xml"
    if os.path.isfile( pyramid_path ):
        print( ' found stitched layer!' )
        layerTree = ET.ElementTree(file=pyramid_path)
        layerRoot = layerTree.getroot()
        has_px_size = False
        for element in layerRoot:
            if ( element.tag == 'imageset' ):
                layerNumber = element.attrib['levels']
                width = element.attrib['width']
                height = element.attrib['height']
                gridWidth = round( int( element.attrib['width'] ) / int( element.attrib['tileWidth'] ) )
                gridHeight = round( int( element.attrib['height'] ) / int( element.attrib['tileHeight'] ) )
                print( "  layer count: {}".format(layerNumber) )
                print( "  image size: {} x {} px (Grid: {} x {})".format(width, height, gridWidth, gridHeight) )
            for subelement in element:
                if ( subelement.tag == 'pixelsize' ):
                    for subsubelement in subelement:
                        if ( subsubelement.tag == 'x' ):
                            scaleX = float( subsubelement.text )*10**9
                            has_px_size = True
                        if ( subsubelement.tag == 'y' ):
                            scaleY = float( subsubelement.text )*10**9
                    print("  Scale : {} nm per pixel".format(scaleX) )
                    break
        if not has_px_size:
            print( 'enter scale (nm per pixel): ' )
            scaleX = float(input())
            scaleY = scaleX
        combineImagesPython( layer_dir, layer_dir, HDView_dir, width, height, scaleX, scaleY, gridWidth, gridHeight, layerNumber, title )
    else:
        print( 'unable to find {}'.format(pyramid_path) )

### actual program start
if __name__ == '__main__':
    #### global var definitions
    root = tk.Tk()
    root.withdraw()

    voxelSizeX          = 0
    voxelSizeY          = 0
    resX                = 0
    resY                = 0

    runImageJ_Script    = True #False
    removeCurtaining    = 1
    createLogVideos     = "n"
    showDebuggingOutput = False
    outputType          = 0 # standard output type (y-axis value) is area-%
    thresholdLimit      = 140
    infoBarHeight       = 0
    metricScale         = 0
    pixelScale          = 0
    startFrame          = 0
    endFrame            = 0
    forcedScaleFactor   = 1
    imageSizeLimit      = 2
    singleDataSet       = False

    ### global settings
    programInfo()
    processArguments()
    if ( showDebuggingOutput ) : print( "I am living in '" + home_dir + "'" )

    if singleDataSet:
        wds_title = 'Please select the subfolder in the "(stiched)" dataset directory containing "HDView.htm"'
    else:
        wds_title = 'Please select the image / working directory'

    print(wds_title)
    workingDirectory = filedialog.askdirectory(title=wds_title).replace('/', os.sep)

    if ( workingDirectory != "" ) :
        print( "Selected working directory: " + workingDirectory )
        if singleDataSet:
            readSingleDataSet( workingDirectory )
        else:
            readProjectData( workingDirectory )

    else:
        print("No directory selected")


    print("-------")
    print("DONE!")

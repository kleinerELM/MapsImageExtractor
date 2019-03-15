
gridWidth = 8;
gridHeight = 6
workingFolder = "D:\\Maps\\C3S 7d Harz\\LayersData\\Layer\\Tile Set";
outputFolder = "D:\\Maps\\C3S 7d Harz\\Output";
filenamePattern = "Tile_{rrr}-{ccc}-000000_0-000.tif";

run("MIST", "gridwidth=" + gridWidth + " gridheight=" + gridHeight + " starttilerow=1 starttilecol=1 imagedir=[" + workingFolder + "] filenamepattern=" + filenamePattern + " filenamepatterntype=ROWCOL gridorigin=UL assemblefrommetadata=false globalpositionsfile=[] numberingpattern=HORIZONTALCOMBING startrow=0 startcol=0 extentwidth=8 extentheight=6 timeslices=0 istimeslicesenabled=false outputpath=[" + outputFolder + "] displaystitching=true outputfullimage=true outputmeta=true outputimgpyramid=false blendingmode=LINEAR blendingalpha=NaN outfileprefix=img- programtype=CUDA numcputhreads=12 loadfftwplan=true savefftwplan=true fftwplantype=MEASURE fftwlibraryname=libfftw3 fftwlibraryfilename=libfftw3.dll planpath=[C:\\Users\\Florian Kleiner\\Documents\\Fiji.app\\lib\\fftw\\fftPlans] fftwlibrarypath=[C:\\Users\\Florian Kleiner\\Documents\\Fiji.app\\lib\\fftw] stagerepeatability=200 horizontaloverlap=11.0 verticaloverlap=11.0 numfftpeaks=0 overlapuncertainty=NaN isusedoubleprecision=true isusebioformats=false issuppressmodelwarningdialog=false isenablecudaexceptions=false translationrefinementmethod=SINGLE_HILL_CLIMB numtranslationrefinementstartpoints=16 headless=false loglevel=MANDATORY debuglevel=NONE");
selectWindow("img-Full_Stitching_Image");
// Macro for ImageJ 1.52d for Windows
// written by Florian Kleiner 2019
// run from command line as follows
// ImageJ-win64.exe -macro "C:\path\to\easyCombine.ijm" "D:\path\to\layer\|D:\path\to\output\|scaleX|scaleY|width|height|gridWidth|gridHeight|title|layerNumber|scaleFactor"


macro "REMPorenanalyse" {
	// check if an external argument is given or define the options
	arg = getArgument();
	if ( arg == "" ) {
		print("This script expects arguments! none given!")
	} else {
		arg_split		= split( getArgument(),"|" );
		dir				= arg_split[0] + "0/data/";
		outputDir		= arg_split[1];
		scaleX			= arg_split[2];
		scaleY			= arg_split[3];
		width			= arg_split[4];
		height			= arg_split[5];
		gridWidth		= arg_split[6];
		gridHeight		= arg_split[7];
		title			= arg_split[8];
		layerNumber		= parseInt(arg_split[9])-1;
		scaleFactor		= arg_split[10];
		
		folderNamePattern = "l_" + layerNumber + "/c_{c}/";
		fileNamePattern = "tile_{r}.tif";
		
		//workingFolder = "D:\\Maps\\C3S 7d Harz\\LayersData\\Layer\\Tile Set";
		//outputFolder = "D:\\Maps\\C3S 7d Harz\\Output";
		
		print( "Starting process using the following arguments..." );
		print( "Directory: " + dir );
		print( "Output directory: " + outputDir );
		print( "Parent directory: " + File.getParent(dir) );
		print( "Image size: " + width + "x" + height + " px" );
		print( "Grid size: " + gridWidth + "x" + gridHeight );
		print( "Scale factor: " + scaleFactor + "x" );
		print( "" );
		
		filePath = dir + "l_" + layerNumber + "/c_0/tile_0.tif";;
		open(filePath);
		bitDep = "8-bit";
		if ( bitDepth() == 16 ) {
			bitDep = "16-bit";
		} else if ( bitDepth() == 24 ) {
			bitDep = "RGB";
		}
		close();
		print( "Creating Image '" + title + "' (" + bitDep + ") ..." );
		newImage( "title", bitDep + " black", width*scaleFactor, height*scaleFactor, 1 );
		mainImageId = getImageID();

		print( "Set scale 1 px = '" + scaleX + " nm" );
		run( "Properties...", "unit=nm pixel_width=" + scaleX + " pixel_height=" + scaleY + "" );
		
		//directory handling
		File.makeDirectory(outputDir);
		
		setBatchMode(true);
		
		print( "Importing image tiles..." );
		for ( i=0; i<=gridWidth; i++ ) {
			path = "l_" + layerNumber + "/c_" + i + "/";
			for ( j=0; j<=gridHeight; j++ ) {
				file="tile_" + j +".tif"; // replace( folderNamePattern, "\{r\}", j );
				filePath = dir + path + file;
				print( " processing: " + filePath );
				if ( File.exists( filePath ) ) {
					print( "  File found, opening..." );
					open(filePath);
					imageId = getImageID();
					
					width	= getWidth();
					height	= getHeight();
					if ( scaleFactor != 1 ) {
						run("Scale...", "x=" + scaleFactor + " y=" + scaleFactor + " interpolation=Bilinear average create");
					}
					
					run("Select All");
					run("Copy");
					
					selectImage( mainImageId );
					makeRectangle(i*width*scaleFactor, j*height*scaleFactor, width*scaleFactor, height*scaleFactor);
					run("Paste");
					
					//////////////////////
					// close the file
					//////////////////////
					print( "  closing file ..." );
					selectImage(imageId);
					close();
					print( "" );
				} else {
					print( "  File missing!");
				}
			}
		}
		
		saveAs("Tiff", outputDir + "/" + title + ".tif" );
	}


	// exit script
	print("Done!");
	if ( arg != "" ) {
		run("Quit");
	}
}



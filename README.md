# MapsImageExtractor
Extracting whole images from a Thermofisher Scientific (formerly FEI) MAPS project and generating Tiff images in the root folder of these projects.
Expecting the "MapsProject.xml" in the root folder.

This scripts reads the scaling of the images and saves them as metadata in the image in a form readable by ImageJ. It also resizes the canvas, if the image exceeds 2 Gigapixel by a factor of 0.5, since ImageJ would be unable to open these files.
A thumbnail with a x-resolution of 2000 pixel will be saved in a folder called thumbnails in the root folder of the project.

# dependencies

This project depends on other Repositories. 

https://github.com/kleinerELM/tiff_scaling
https://github.com/kleinerELM/image_recobination

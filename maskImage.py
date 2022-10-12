from astropy.io import fits
import sys

image_filename = sys.argv[2]
output_filename = image_filename.replace('p', 'm')
mask_filename = sys.argv[1]

imagelist = fits.open(image_filename)
masklist = fits.open(mask_filename)

mask = masklist[0].data*32760.0
imagelist[0].data = imagelist[0].data + mask

imagelist.writeto(output_filename)

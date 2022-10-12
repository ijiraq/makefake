from astropy.io import fits
from astropy import units


from astropy.nddata import CCDData
import ccdproc
import sys

ccd = int(sys.argv[2])
filename = sys.argv[1]
hdulist = fits.open(filename)
hdu = hdulist[0]

data = hdu.data
data[data>0] = 1
mask = ccdproc.ccdmask(data)
mask_as_ccd = CCDData(data=mask.astype('uint8'), unit=units.dimensionless_unscaled)
mask_as_ccd.header['EXPTYPE']='MASK'
mask_as_ccd.write(f'm{ccd:02d}.fits')


"""
Make an image mask based on where there are 'zeros' in the FLAT.  Set the bits on those masked pixels using LSST MASK BITS
"""

LSST_MASK_BITS = {'BAD': 0,
                  'SAT': 1,
                  'INTRP': 2,
                  'EDGE': 4,
                  'DETECTED': 5,
                  'DETECTED_NEGATIVE': 6,
                  'SUSPECT': 7,
                  'NO_DATA': 8,
                  'CROSSTALK': 9,
                  'NOT_BLENDED': 10,
                  'UNMASKEDNAN': 11,
                  'BRIGHT_OBJECT': 12,
                  'CLIPPED': 13,
                  'INEXACT_PSF': 14,
                  'REJECTED': 15,
                  'SENSOR_EDGE': 16,
                  }

from astropy.io import fits
from astropy.nddata import CCDData
import ccdproc
import sys

ccd = int(sys.argv[2])
hdulist = fits.open(sys.argv[1])
hdu = hdulist[ccd+1]

mask = ccdproc.ccdmask(hdu.data)
mask_as_ccd = CDData(data=mask.astype('uint8'))
mask_as_ccd.header['EXPTYPE']='MASK'
mask_as_ccd.write(f'm{ccd:02d}.fits')

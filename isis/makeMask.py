"""
Make an image mask based on where there are 'zeros' in the FLAT.  Set the bits on those masked pixels using LSST MASK BITS
"""
import re
from scipy import ndimage
import numpy
from astropy import units
from astropy.io import fits
from astropy.nddata import CCDData
import ccdproc
import argparse

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


def main(image):
    """
    run the script
    """
    mask = {}
    padding = 9
    with fits.open(image) as hdulist:
        i_hdu = hdulist[0]
        # mask['BAD'] = (ccdproc.ccdmask(i_hdu.data)) * 2**LSST_MASK_BITS['BAD']
        mask['NO_DATA'] = (i_hdu.data == 0) * 2**LSST_MASK_BITS['NO_DATA']
        mask['NO_DATA'] = ndimage.generic_filter(mask['NO_DATA'], max, size=padding)
        mask['SAT'] = (i_hdu.data > 32000) * 2**LSST_MASK_BITS['SAT']
        mask['SAT'] = ndimage.generic_filter(mask['SAT'], max, size=padding)
        # datasec = i_hdu.header['DATASEC']
        # match = re.match(r'\[(\d+):(\d+),(\d+):(\d+)]', datasec)
        # x1, x2, y1, y2 = [int(x) for x in match.groups()]
        # mask['SENSOR_EDGE'] = i_hdu.data * 0 + 2**LSST_MASK_BITS['SENSOR_EDGE']
        # mask['SENSOR_EDGE'][y1-1:y2-2, x1-1:x2-2] = 0
        mask['BRIGHT_OBJECT'] = ((i_hdu.data > 3000) & (i_hdu.data < 40000)
                                 )*2**LSST_MASK_BITS['BRIGHT_OBJECT']
        mask['SAT'] = ndimage.generic_filter(mask['SAT'], max, size=padding)

    masked = numpy.sum([mask[k] for k in mask], axis=0)
    out_filename = f"mask_{image}"
    mask_as_ccd = CCDData(data=masked.astype('uint32'), unit=units.dimensionless_unscaled)
    mask_as_ccd.header = fits.open(image)[0].header
    mask_as_ccd.header['EXPTYPE'] = 'MASK'
    for key in LSST_MASK_BITS:
        mask_as_ccd.header[key] = LSST_MASK_BITS[key]
    mask_as_ccd.write(out_filename, output_verify='fix', overwrite=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Using the input image and a mask to apply to image before running ISIS""")
    parser.add_argument('image', help="Filename of the image to build mask for")
    args = parser.parse_args()
    main(args.image)

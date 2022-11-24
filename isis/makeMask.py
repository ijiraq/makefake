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


def main(image, maskfile=None, maskbits=['NO_DATA', 'SAT', 'BRIGHT_OBJECT']):
    """
    run the script
    """
    mask = {}
    padding = 9
    with fits.open(image) as hdulist:

        i_hdu = hdulist[0]
        if 'NO_DATA' in maskbits:
            mask['NO_DATA'] = (i_hdu.data == 0) * 2**LSST_MASK_BITS['NO_DATA']
            mask['NO_DATA'] = ndimage.generic_filter(mask['NO_DATA'], max, size=padding)
        if 'BAD' in maskbits:
            mask['BAD'] = (ccdproc.ccdmask(i_hdu.data)) * 2**LSST_MASK_BITS['BAD']
        if 'SAT' in maskbits:
            mask['SAT'] = (i_hdu.data > 32000) * 2**LSST_MASK_BITS['SAT']
            mask['SAT'] = ndimage.generic_filter(mask['SAT'], max, size=padding)
        if 'SENSOR_EDGE' in maskbits:
            datasec = i_hdu.header.get('DATASEC', None)
            if dataset is not None:
                match = re.match(r'\[(\d+):(\d+),(\d+):(\d+)]', datasec)
                x1, x2, y1, y2 = [int(x) for x in match.groups()]
                mask['SENSOR_EDGE'] = i_hdu.data * 0 + 2**LSST_MASK_BITS['SENSOR_EDGE']
                mask['SENSOR_EDGE'][y1-1:y2-2, x1-1:x2-2] = 0
        if 'BRIGHT_OBJECT' in maskbits:
            mask['BRIGHT_OBJECT'] = ((i_hdu.data > 3000) & (i_hdu.data < 40000))*2**LSST_MASK_BITS['BRIGHT_OBJECT']
            mask['BRIGHT_OBJECT'] = ndimage.generic_filter(mask['BRIGHT_OBJECT'], max, size=padding)


    masked = numpy.sum([mask[k] for k in mask], axis=0)
    if maskfile is not None:
        with fits.open(maskfile) as hdulist:
            masked = masked.astype('uint32') | hdulist[0].data.astype('uint32')
        out_filename = f"mask_{maskfile}"
    else:
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
    parser.add_argument('--maskfile', default=None, type=str, help="Mask filename to augment")
    parser.add_argument('--maskbits', nargs='*', help="Which bits to mask?", choices=LSST_MASK_BITS.keys())
    args = parser.parse_args()
    main(args.image, args.maskfile)

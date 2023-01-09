"""
Make an image mask based on where there are 'zeros' in the FLAT.  Set the bits on those masked pixels using LSST MASK BITS
"""
import re
from scipy import ndimage
import numpy
import logging
from astropy import units
from astropy.io import fits
from astropy.nddata import CCDData
import ccdproc
import argparse
from stack import get_flag_map


def main(image, maskfile=None, maskbits=['NO_DATA', 'SAT', 'BRIGHT_OBJECT']):
    """
    run the script
    """
    mask = {}
    padding = 9
    with fits.open(image) as hdulist:

        i_hdu = hdulist[1]
        m_hdu = hdulist[2]
        flag_map = get_flag_map(m_hdu)
        v_hdu = hdulist[3]
        logging.debug(f"Working on {image}")
        if 'NO_DATA' in maskbits:
            logging.info(f"Masking NO_DATA")
            mask['NO_DATA'] = (i_hdu.data == 0) * 2**flag_map['NO_DATA']
            mask['NO_DATA'] = ndimage.generic_filter(mask['NO_DATA'], max, size=padding)
        if 'BAD' in maskbits:
            logging.info(f"Masking BAD")
            mask['BAD'] = (ccdproc.ccdmask(i_hdu.data)) * 2**flag_map['BAD']
        if 'SAT' in maskbits:
            logging.info(f"Masking SAT")
            mask['SAT'] = (i_hdu.data > 32000) * 2**flag_map['SAT']
            mask['SAT'] = ndimage.generic_filter(mask['SAT'], max, size=padding)
        if 'SENSOR_EDGE' in maskbits:
            logging.info(f"Masking SENSOR_EDGE")
            datasec = i_hdu.header.get('DATASEC', None)
            if datasec is not None:
                match = re.match(r'\[(\d+):(\d+),(\d+):(\d+)]', datasec)
                x1, x2, y1, y2 = [int(x) for x in match.groups()]
                mask['SENSOR_EDGE'] = i_hdu.data * 0 + 2**flag_map['SENSOR_EDGE']
                mask['SENSOR_EDGE'][y1-1:y2-2, x1-1:x2-2] = 0
        if 'BRIGHT_OBJECT' in maskbits:
            logging.info(f"Masking BRIGHT_OBJECT")
            mask['BRIGHT_OBJECT'] = ((v_hdu.data > 3000) & (v_hdu.data < 40000))*2**flag_map['BRIGHT_OBJECT']
            mask['BRIGHT_OBJECT'] = ndimage.generic_filter(mask['BRIGHT_OBJECT'], max, size=padding)
        out_filename = f"mask_{maskfile}.fits"
        logging.info(f"Writing results to {out_filename}")
        masked = numpy.sum([mask[k] for k in mask], axis=0)
        m_hdu.data = masked.astype('uint32') | m_hdu.data.astype('uint32')
        hdulist.writeto(out_filename, output_verify='fix', overwrite=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Using the input image and a mask to apply to image before running ISIS""")
    parser.add_argument('image', help="Filename of the image to build mask for")
    parser.add_argument('--maskfile', default=None, type=str, help="Mask filename to augment")
    parser.add_argument('--maskbits', nargs='*', help="Which bits to mask?")
    parser.add_argument('--log-level', choices=['INFO','DEBUG','ERROR'], default='ERROR')
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging,args.log_level))
    main(args.image, args.maskfile, maskbits=args.maskbits)

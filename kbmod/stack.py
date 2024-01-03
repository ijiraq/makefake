import argparse
import logging
import os
from collections import OrderedDict
from reproject import reproject_interp
from reproject.mosaicking import reproject_and_coadd
import numpy as np
from astropy import time, units
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.nddata import VarianceUncertainty, bitfield_to_boolean_mask
from astropy.table import QTable
from astropy.wcs import WCS
from ccdproc import CCDData, wcs_project, Combiner
import warnings
numpy = np
previous_snapshot = None
__version__ = 0.1

STACKING_MODES = {'MEDIAN': np.nanmedian, 'MEAN': np.nanmean, 'SUM': np.nansum, 'MAX': np.nanmax,
                  'DEFAULT': np.nanmedian, 'WEIGHTED_MEDIAN': None}
PRIMARY = 0
IMAGE = 1
MASK = 2
VAR = 3
WEIGHT = 'weight'
MASK_FLAGS = ['BAD', 'EDGE', 'NO_DATA', 'BRIGHT_OBJECT', 'SAT', 'INTRP', 'REJECTED', 'NOT_DEBLENDED']


def _weighted_quantile(values, quantile, sample_weight):
    """ Very close to numpy.percentile, but supports weights.
    Always overwrite=True, works on arrays with nans.

    # THIS IS NOT ACTUALLY THE PERCENTILE< BUT CLOSE ENOUGH...<

    this was taken from a stackoverflow post:
    https://stackoverflow.com/questions/21844024/weighted-percentile-using-numpy

    NOTE: quantiles should be in [0, 1]!

    :param values: numpy.array with data
    :param quantile: array-like with many quantiles needed
    :param sample_weight: array-like of the same length as `array`
    :return: numpy.array with computed quantiles.
    """
    logging.info(f'computing weighted quantile: {quantile}')
    sorter = np.argsort(values, axis=0)
    values = numpy.take_along_axis(values, sorter, axis=0)
    sample_weight = numpy.take_along_axis(sample_weight, sorter, axis=0)
    # check for inf weights, and remove
    sample_weight[numpy.isinf(sample_weight)] = 0.0
    weighted_quantiles = np.nancumsum(sample_weight, axis=0) - 0.5 * sample_weight
    weighted_quantiles /= np.nansum(sample_weight, axis=0)
    ind = np.argmin(weighted_quantiles <= quantile, axis=0)
    return np.take_along_axis(values, np.expand_dims(ind, axis=0), axis=0)[0]


def coadd(mosaic, stamp):
    """
    add stamp into mosaic by projecting stamp to main and then adding.
    :param fits.ImageHDU mosaic: the control / main image
    :param fits.ImageHDU stamp: the stamp to add to main
    """
    array, footprint = reproject_and_coadd([main, stamp],
                                           output_projection=mosaic.header,
                                           reproject_function=reproject_interp,
                                           combine_function='sum')
    mosaic.data = array
    return


def swarp(hdus, rate, stacking_mode="MEAN"):
    """
    use the WCS to project all image to the wcs of the first HDU shifting the CRVAL of each image by rate*dt
    :param OrderDict hdus: a dictionary of hdulists, the dictionary 'IMAGE' keyword from the PRIMARY HDU
    of the fits file in the hdulist
    :param dict rate: dictionary with the ra/dec shift rates.
    :param str stacking_mode: what process to use for combining images MEAN or MEDIAN
    :return: fits.HDUList
    """
    # Project the input images to the same grid using interpolation
    # logging.debug(f"Called with {kwargs}")
    if stacking_mode not in ['MEDIAN', 'MEAN']:
        logging.warning(f'{stacking_mode} not available for swarp stack. Setting to MEAN')
        stacking_mode = 'MEAN'
    reference_hdu = hdus[next(iter(hdus))]
    reference_date = mid_exposure_mjd(reference_hdu[PRIMARY])
    reference_wcs = WCS(reference_hdu[IMAGE].header)
    stack_input = {}
    logging.debug(f'stacking at rate/angle set: {rate}')
    ccd_data = {}

    for image in hdus:
        # logging.info(f"Opening {image} to add to stack")
        # with fits.open(image, mode='update') as hdu:
        hdu = hdus[image]
        wcs_header = hdu[IMAGE].header
        # wcs_header = hdu[1].header.copy()
        dt = (mid_exposure_mjd(hdu[PRIMARY]) - reference_date)
        logging.debug(f"image: {image}")
        logging.debug(f"DT: {dt}")
        logging.debug(f"dra:{(rate['dra'] * dt).to('arcsec').value * numpy.cos(numpy.deg2rad(wcs_header['CRVAL2']))}")
        logging.debug(f"dra:{(rate['ddec'] * dt).to('arcsec').value}")
        wcs_header['CRVAL1'] -= (rate['dra'] * dt).to('degree').value * numpy.cos(
            numpy.deg2rad(wcs_header['CRVAL2']))
        wcs_header['CRVAL2'] -= (rate['ddec'] * dt).to('degree').value
        for layer in [IMAGE, MASK, VAR]:
            data = hdu[layer].data
            if layer == VAR:
                data = VarianceUncertainty(data)
            elif layer == MASK:
                mask_bits = []
                flag_map = get_flag_map(hdu[layer])
                for FLAG in MASK_FLAGS:
                    mask_bits.append(2**flag_map[FLAG])
                data = bitfield_to_boolean_mask(data,
                                                ignore_flags=mask_bits,
                                                flip_bits=True)
            ccd_data[layer] = data
        # for i in range(ccd_data[MASK].shape[0]):
        #    for j in range(ccd_data[MASK].shape[1]):
        #        sys.stderr.write(f"{ccd_data[MASK][i,j]} ")
        #    sys.stderr.write('\n')
        # sys.stderr.write('*'*60)
        # sys.stderr.write('\n')
        logging.debug(f'Adding {hdu[0].header["IMAGE"]} to projected stack.')

        if True:
            stack_input[image] = wcs_project(CCDData(ccd_data[IMAGE],
                                                     mask=ccd_data[MASK],
                                                     header=wcs_header,
                                                     wcs=WCS(wcs_header),
                                                     unit='adu',
                                                     uncertainty=ccd_data[VAR]),
                                             reference_wcs)
            # logging.debug(f"{image} data:{stack_input[image].data}")
            # sys.exit()
    combiner = Combiner(stack_input.values())
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        if stacking_mode == 'MEDIAN':
            stacked_image = combiner.median_combine()
        else:
            stacked_image = combiner.average_combine()
    logging.debug(f"stacked_image: {stacked_image}")
    logging.debug(f"stacked_image.mask: {stacked_image.mask}")
    logging.debug(f"stacked_image.data: {stacked_image.data}")
    logging.debug(f"type: {type(stacked_image)}")
    return fits.ImageHDU(data=stacked_image.data, header=reference_hdu[IMAGE].header)


def mid_exposure_mjd(hdu, mjd_keyword='MJD-OBS', exptime_keyword='EXPTIME'):
    mjd_start = time.Time(hdu.header[mjd_keyword], format='mjd').utc
    return mjd_start + (hdu.header[exptime_keyword]/2)*units.second


def get_flag_map(mask_hdu) -> dict:
    """
    Given a mask HDU that is formated like an LSST mask plane return the dictionary that maps flags to bits

    :param ImageHDU mask_hdu: the MASK HDU to get the dictionary from
    """
    mask_bits = {}
    for key in mask_hdu.header['MP_*']:
        mask_bits[key.replace('MP_', '')] = mask_hdu.header[key]
    return mask_bits


def crop(hdu, centre, box_size):
    """
    Crop the image at centre with square of size
    :param fits.ImageHDU hdu: the HDU containing the data extensiosn to crop
    :param SkyCoord centre: the centre of the crop section
    :param int box_size: the half dimension the section to crop out.

    """
    w = WCS(hdu.header)
    x, y = w.all_world2pix(centre.ra.degree, centre.dec.degree, 0)
    x1 = int(max(0, x - box_size))
    x2 = int(min(hdu.header['NAXIS1'], x1 + 2 * box_size))
    x1 = int(max(0, x2 - 2 * box_size))
    y1 = int(max(0, y - box_size))
    y2 = int(min(hdu.header['NAXIS2'], y1 + 2 * box_size))
    y1 = int(max(0, y2 - 2 * box_size))
    logging.debug(f'{centre.to_string(style="hmsdms", sep=":")} -> ({x},{y})[{y1}:{y2},{x1}:{x2}]')
    if y2 - y1 < 1 or x2 - x1 < 1:
        raise ValueError("No data in section.")
    img = fits.ImageHDU(header=hdu.header)
    img.header['XOFFSET'] = x1
    img.header['YOFFSET'] = y1
    img.header['CRPIX1'] -= x1
    img.header['CRPIX2'] -= y1
    img.data = hdu.data[y1:y2, x1:x2]
    return img


def main(image_list, results, outfile, stack_mode, n_sub_stacks, clip, section_size):
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    logging.info(f'Writing results to {args.outfile}')

    stack_function = swarp
    result_table = QTable.read(results)
    images = image_list
    box_size = section_size * 2
    # Organize images in MJD order.
    mjds = []
    logging.info(f"Sorting list of {len(images)} based on mjd")
    new_images = []
    full_hdus = OrderedDict()
    for filename in images:
        try:
            hdulist = fits.open(filename)
            image = os.path.basename(filename)
            full_hdus[image] = hdulist
            full_hdus[image][PRIMARY].header['IMAGE'] = image
            mjds.append(mid_exposure_mjd(hdulist[PRIMARY]))
            new_images.append(image)
        except Exception as ex:
            logging.error(str(ex))
            logging.error(f"Failed to open {filename} not using")

    ind = np.argsort(mjds)
    # sort the images by mjd
    images = numpy.array(new_images)[ind]
    logging.info(f"Sorted list of {len(mjds)} dates.")
    # In debug mode just do three images or less if there aren't three
    if logging.getLogger().getEffectiveLevel() < logging.INFO:
        num_of_images = min(6, len(images))
        stride = max(1, int(len(images) / num_of_images - 1))
        logging.debug(f'Selecting every {stride}th images, for total of {num_of_images}')
        images = images[::stride]

    # do the stacking in groups of images as set from the CL.
    for group_index in range(n_sub_stacks):
        # stride the image list
        start_idx = len(images) // n_sub_stacks * group_index
        start_idx = int(max(0, start_idx))
        end_idx = len(images) // args.n_sub_stacks * (group_index + 1)
        end_idx = int(min(len(images), end_idx))
        sub_images = images[start_idx:end_idx]
        reference_hdu = full_hdus[sub_images[0]]
        output_hdulist = fits.HDUList()
        output_hdulist.append(fits.PrimaryHDU())

        hdus = OrderedDict()
        for image in sub_images:
            hdus[image] = full_hdus[image]
        ref = hdus[next(iter(hdus))][1]
        output_hdulist.append(fits.ImageHDU(data=ref.data*0,
                                            header=ref.header))

        count = 0
        total = len(result_table)
        for row in result_table:
            count += 1
            logging.info(f"Doing {count:06d} of {total:06d}")
            # make a dictionary of the astrometric headers.
            centre = SkyCoord(row['ra'], row['dec'], frame='icrs')
            ra, dec = WCS(reference_hdu[IMAGE].header).all_pix2world([0, row['x_v'].value], [0, row['y_v'].value], 0)
            dra = (ra[1]-ra[0])*units.deg/units.pix * row['x_v'].unit
            ddec = (dec[1]-dec[0])*units.deg/units.pix * row['y_v'].unit
            logging.debug(f"Doing cutouts around {centre} at rates {dra},{ddec}")
            chdus = OrderedDict()
            for key in hdus:
                hdu = hdus[key]
                hdul = fits.HDUList()
                hdul.append(fits.PrimaryHDU(header=hdu[PRIMARY].header))
                for idx in [IMAGE, MASK, VAR]:
                    hdul.append(crop(hdu[idx], centre, box_size))
                chdus[key] = hdul

            if clip is not None:
                # Use the variance data section to mask high variance pixels from the stack.
                # mask pixels that are both high-variance AND part of a detected source.
                logging.debug(f'Masking pixels in image whose variance exceeds {clip} times the median variance.')
                for key in chdus:
                    # with fits.open(key, mode='update') as hdu:
                    hdu = chdus[key]
                    flag_map = get_flag_map(hdu[MASK])
                    if hdu[IMAGE].header.get('CLIP', None) is not None:
                        continue
                    hdu[IMAGE].header['CLIP'] = clip
                    # hdu.flush()
                    mvar = numpy.nanmedian(hdu[VAR].data)
                    if numpy.isnan(mvar):
                        logging.warning(f"median varianace of {key} is {mvar}")
                    logging.debug(f'Median variance of {key} is {mvar}')
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        bright_mask = hdu[VAR].data > mvar * clip
                    detected_mask = bitfield_to_boolean_mask(hdu[MASK].data,
                                                             ignore_flags=flag_map['DETECTED'],
                                                             flip_bits=True)
                    logging.debug(f'Bright Mask flagged {np.sum(bright_mask)}')
                    hdu[IMAGE].data[bright_mask & detected_mask] = np.nan
                    logging.debug(f'Clip setting {np.sum(bright_mask & detected_mask)} to nan')
                    hdu[IMAGE].data[bright_mask & detected_mask] = np.nan
                    # update the local version with the clipped data, but not if this is a cutout.

            output = stack_function(chdus, {'dra': dra, 'ddec': ddec}, stacking_mode=stack_mode)
            output = crop(output, centre, section_size)
            coadd(output_hdulist[1], output)
            output.header['SOFTWARE'] = f'{__name__}-{__version__}'
            output.header['NCOMBINE'] = (len(chdus), 'Number combined')
            output.header['COMBALGO'] = (stack_mode, 'Stacking mode')
            output.header['DRA'] = (dra.value, str(dra.unit))
            output.header['DDEC'] = (ddec.value, str(ddec.unit))
            output.header['ASTLEVEL'] = 1
            output_hdulist.append(output)

            output_hdulist.writeto(f"{outfile}_{group_index}.fits", overwrite=True)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     fromfile_prefix_chars='@')
    parser.add_argument('image_list', nargs='+', help="List of DIFFEXP images to stack.")
    parser.add_argument('results', help="KBMOD results file (in ECSV format) with ra/dec and x_v/y_v rates.")
    parser.add_argument('outfile', help="Name of the file that will hold the stamps.")
    parser.add_argument('--stack-mode', choices=STACKING_MODES.keys(),
                        default='WEIGHTED_MEDIAN', help="How to combine images.")
    parser.add_argument('--n-sub-stacks', default=3, type=int, help='How many sub-stacks should we produce')
    parser.add_argument('--clip', type=int, default=None,
                        help='Mask pixel whose variance is clip times the median variance, DEFAULT=%(default)s')
    parser.add_argument('--section-size', type=int, default=21,
                        help='Break images into section when stacking (conserves memory)')
    parser.add_argument('--log-level', help="What level to log at?", default="ERROR",
                        choices=['INFO', 'ERROR', 'DEBUG'])

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level),
                        format="%(asctime)s :: %(levelname)s :: %(module)s.%(funcName)s:%(lineno)d %(message)s")
    logging.debug(f"Args: {args}")
    main(args.image_list, args.results, args.outfile, args.stack_mode,
         args.n_sub_stacks, args.clip, args.section_size)

from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u
import sys
import os
import sip_tpv
import numpy
import argparse
import logging
import ccdproc


def main():
    parser = argparse.ArgumentParser(
        description=
        f"Build DIFFEXP by assembling DIFF/MASK and VARIANCE into an MEF."
        f""
        f"The VARIANCE plane is built from an analysis of the original image (ignores difference template variance)",

        fromfile_prefix_chars='@')

    parser.add_argument(
        "primary", help="base image, used for header keyword values")
    parser.add_argument(
        "interp_filename",  help="The file with base image swarped to common gird")
    parser.add_argument(
        "diff_filename",  help="The subtracted image, from ISSIS (conv_interp_????)")
    parser.add_argument(
        "mask_filename",  help="The MASK image")

    args = parser.parse_args()
    build_mef(args.primary, args.interp_filename, args.diff_filename, args.mask_filename)


def build_mef(primary: str, interp_filename: str, diff_filename: str, mask_filename: str) -> str:
    """

    :param primary: the primary image this is the DIFFEXP for
    :param interp_filename: the swarped version of primary (inter_)
    :param diff_filename: the difference image
    :param mask_filename: the mask image for this difference

    :return: DIFF filename

    """
    print(primary)
    with fits.open(primary) as hdulist:
        header = hdulist[0].header

    diff_hdulist = fits.HDUList()
    diff_hdulist.append(fits.PrimaryHDU(header=header))

    # get the WCS and variance from the interp image
    # this ignores variance coming from the co-add image
    with fits.open(interp_filename) as interp:
        sip_tpv.pv_to_sip(interp[0].header)
        wcs_header = WCS(interp[0].header).to_header()
        var = ccdproc.CCDData(interp[0].data, unit=u.adu)
        var = ccdproc.create_deviation(var, gain=1.6*u.electron/u.adu, readnoise=5*u.electron) 
        var = var.uncertainty.array**2
        var[interp[0].data == 0] = 0

    # get the difference image
    # set the WCS using the interp_ image
    with fits.open(diff_filename) as conv_hdulist:
        conv_hdulist[0].data *= -1
        for keyword in wcs_header:
            conv_hdulist[0].header[keyword] = wcs_header[keyword]
            conv_hdulist[0].header['EXTTYPE'] = 'IMAGE'
        diff_hdulist.append(fits.ImageHDU(header=conv_hdulist[0].header, data=conv_hdulist[0].data))

    # add the mask plane, wcs from interp_
    with fits.open(mask_filename) as conv_hdulist:
        conv_hdulist[0].data = conv_hdulist[0].data * numpy.array([1]).astype('uint32')
        for keyword in wcs_header:
            conv_hdulist[0].header[keyword] = wcs_header[keyword]
        conv_hdulist[0].header['EXTTYPE'] = 'MASK'
        diff_hdulist.append(fits.ImageHDU(header=conv_hdulist[0].header, data=conv_hdulist[0].data))
        del (conv_hdulist[0].header['BITPIX'])
        diff_hdulist.append(fits.ImageHDU(header=conv_hdulist[0].header, data=var))
        diff_hdulist[-1].header['EXTTYPE'] = 'VARIANCE'

    expnum = diff_hdulist[0].header['EXPNUM']
    ccdnum = diff_hdulist[0].header["EXTVER"]
    diff_image = f"DIFFEXP-{expnum}-{ccdnum:02d}.fits"
    diff_hdulist.writeto(diff_image, overwrite=True)
    return diff_image


if __name__ == '__main__':
    main()

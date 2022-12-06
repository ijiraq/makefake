"""
Take an MEF file and write out SIF files in sub-directories named by the extension name keywrod from the MEF.

This is used to take the output of plantImages (MEFs with artificial sources added) into sub-directories that we can run ISIS subtraction on

Usage:  python populate.py /source_dir/fkXXXXXXX.fits

Outputs files to 'ccdXX' directories.
"""

from astropy.io import fits
import sys, os

filename = sys.argv[1]

basename = os.path.splitext(os.path.basename(filename))[0]
dirname = os.path.dirname(filename)

with fits.open(filename, ignore_missing_simple=True, output_verify='fix') as mef:
    for ext in range(1,len(mef)):
        extname = mef[ext].header['EXTNAME']
        extver = mef[ext].header.get('EXTVER', ext-1)
        dir = f"{dirname}/{extname}"
        if not os.access(dir, os.F_OK):
            os.mkdir(dir)
        if basename[-1] in ['p','s']:
            output_filename = f"{basename}{extver:02d}.fits"
        else:
            output_filename = f"{basename}.{extver:02d}.fits"
        if not os.access(f"{dir}/{output_filename}", os.F_OK):
            hdu = fits.PrimaryHDU(header=mef[extname].header, data=mef[extname].data)
            print(f"{filename} -> {dir}/{output_filename}")
            hdu.writeto(f"{dir}/{output_filename}", output_verify='fix')



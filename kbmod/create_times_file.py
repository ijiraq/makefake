import argparse
import re
import os
from astropy import time
from astropy.io import fits
from astropy import units


def create_times_file(img_path, times_filename,
                      pattern="DIFFEXP-(\d{7})-*.fits",
                      time_keyword='MJD-OBS',
                      time_format='mjd',
                      exptime_keyword='EXPTIME', exptime_unit='s'):
    """
    Get list of MJD at middle of exposure for all files in img_path matching pattern and store in file_fn.

    :param str img_path: The directory where the DIFFEXP files are located (can be .)
    :param times_filename: name of file to store the visit-id - mjd mapping into
    :param str pattern: The pattern to match files and include.
    :param str time_keyword: the FITS header keyword holding the MJD of the start of observation
    :param str time_format: the format of time_keyword, passed to astropy.time.Time
    :param str exptime_keyword: the FITS header keyword holding the exposure time (expected in seconds)
    :param str exptime_unit: units of the exposure time (default is 's')
    """

    regex = re.compile(pattern)
    filenames=os.listdir(img_path)
    with open(times_filename, 'w') as out_handle:
        for fn in filter(regex.match, filenames):
            with fits.open(fn) as hdulist:
                mjd = hdulist[0].header[time_keyword]
                exptime = hdulist[0].header[exptime_keyword] * units.Unit(exptime_unit)
                t = time.Time(mjd, format=time_format) + exptime / 2.0
                visit_id = regex.match(fn).group(1)
                print(f'{visit_id} {t.mjd:12.6f}', file=out_handle)


def main():
    """Run create_times_file as a CL task.x"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-path', default=".", help="Directory with input files to make times.dat for.  "
                                                          "(%(default)s)")
    parser.add_argument('--times-file', default='times.dat', help='name of file to store visit->MJD mapping into. '
                                                                  '(%(default)s)')
    parser.add_argument('--visit-regex', default="DIFFEXP-(\d{7})-.*.fits", help="regular expression to select "
                                                                               "desired exposures: (%(default)s)")
    parser.add_argument('--mjd-kw', default="MJD-OBS", help="FITS Keyword with MJD of start of exposure: (%(default)s)")
    args = parser.parse_args()
    create_times_file(args.input_path,
                      args.times_file,
                      args.visit_regex,
                      time_keyword=args.mjd_kw)


if __name__ == '__main__':
    main()

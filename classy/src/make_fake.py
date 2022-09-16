"""
Make a list of fake sources given a reference image and the image to plant into.
"""
import os
import sys

import numpy
import orbit_utils
from astropy import wcs
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table
from astropy.time import Time


def M_at_jday(M, epoch_M, a, jday) -> float:
    """
    Given the current mean anomaly M at epoch_M and the semi-major axis, compute the mean anomaly at jday
    :param M:
    :param epoch_M:
    :param a:
    :param jday:
    :return:
    """

    nu = 2 * numpy.pi / 365.25
    return (M + (jday - epoch_M) * (nu / a ** 1.5)) % (2 * numpy.pi)


ELEMENT_RANGES = {
    'a': (30, 100),
    'e': (0, 0.5),
    'inc': (0, numpy.pi / 2.0),
    'node': (0, 2 * numpy.pi),
    'peri': (0, 2 * numpy.pi),
    'M': (0, 2 * numpy.pi) }


def build_plant_list_catalog(image_filename: str,
                             reference_epoch: int = 2459792,
                             element_ranges: dict = None,
                             mag_limit: float = 27.5,
                             gb: float = 0.15,
                             ext: str = ".plantList") -> None:
    """
    Given the reference image compute the locations of artificial sourcess on the destination image.
    :param image_filename: filename of FITS image to generate a plantlist for.
    :param reference_epoch: epoch (JD) of the reference date for 'M' and used to set the seed of random generator for elements.
    :param element_ranges: ranges of a/e/i/Omega/omega/M to draw from
    :param mag_limit: limiting magnitude to plant source to
    :param gb: slope of phase function in Bowel formulasim that converts H to mag
    :param ext: extension of filename for plantList output, nominall Image_filename.plantList

    The default reference epoch (integer Julian Day) is 2459792 (2022-07-31T12:00:00.000) , this is used to seed the random number
    generator that produces the catalog that will include sources on the current image.   The value of 'M' generated is take to be
    at this epoch and M is propogated to the JD of image_filename
    :return:
    """

    if element_ranges is None:
        element_ranges = ELEMENT_RANGES

    orbits = {}
    for element in element_ranges.keys():
        orbits[element] = []
    orbits['H']  = []

    max_iters = 1E8
    max_objects = 10000
    obs_code = 500

    wcs_dict = {}
    jd_dict = {}
    print(image_filename)
    with fits.open(image_filename) as hdulist:
        extno = 0
        if hdulist[extno].header['NAXIS'] == 0:
            extno = 1
        wcs_dict[image_filename] = wcs.WCS(hdulist[extno].header)
        jd_dict[image_filename] = Time(hdulist[extno].header['MJD-OBS'], format='mjd').jd

    # initialize the random number generator using the JD of the reference frame.
    rnd_gen = numpy.random.default_rng(reference_epoch)

    # compute the location of the observer on the date image_filename was taken.
    obs_pos, vel, ros, ierr = orbit_utils.obspos(obs_code, jd_dict[image_filename])

    nobjects = 0
    niters = 0
    while nobjects < max_objects and niters < max_iters:
        niters += 1
        orbit = {}
        for element in element_ranges:
            orbit[element] = rnd_gen.uniform(element_ranges[element][0],
                                             element_ranges[element][1],
                                             1)
        # Compute the location of the sources on the image_filename date.
        orbit['M'] = M_at_jday(orbit['M'], reference_epoch, orbit['a'], jd_dict[image_filename])
        pos = orbit_utils.pos_cart(orbit['a'],
                                   orbit['e'],
                                   orbit['inc'],
                                   orbit['node'],
                                   orbit['peri'],
                                   orbit['M'])
        delta, RA, DEC, ierr = orbit_utils.radececlxv(pos, obs_pos)
        if ierr != 0 :
            raise OSError(f'Failed to get RA/DEC for {orbit}')
        coord = SkyCoord(RA, DEC, distance=delta, units=('radian', 'radian', 'au'))
        # check if this sources is within the image we are makeing a plantList for.
        if not wcs_dict[image_filename].footprint_contains(coord):
            continue
        nobjects += 1
        r = numpy.sqrt(pos[0] ** 2, pos[1] ** 2 + pos[2] ** 2)
        h_max = mag_limit - 10 * numpy.log10(r)
        h = rnd_gen.uniform(5, h_max)
        orbit['h'] = h
        alpha, mag, ierr = orbit_utils.appmag(r, delta, ros, h, gb)
        if ierr != 0:
            raise OSError(f"Computing AppMag failed for {orbit}")
        orbit['alpha'] =  alpha
        orbit['mag'] = mag

        for element in orbits.keys():
            orbits[element].append(orbit[element])

    catalog_filename = f"{os.path.splitext(image_filename)[0]}.{ext}"
    Table(orbits).write(catalog_filename)


def main():
    dest_image = sys.argv[1]
    print(dest_image)
    build_plant_list_catalog(dest_image)


if __name__ == '__main__':
    main()
"""
Various classes to read the output of the KBMOD astrometry code and create Observation objects

Create an Observation from the 'rough' kbmod astrometry file

The current format of the discovery files is series of entries like the following:

detection #, distance estimate (au), magnitude, visit # (0/1/2), chip, # of detections
        x1 y1 dx1 dy1 mjd1 ra1 dec1 cos(dec)*dra1 ddec1
        X2 y2 dx2 dy2 mjd2 ra2 dec2 cos(dec)*dra2 ddec2
        x3 y3 dx3 dy3 mjd3 ra3 dec3 cos(dec)*dra3 ddec3

The first line is a header line, and the following lines are the measurements of the object.

The current format of the tracking files is series of entries like the following:

chip index mjd x y dx/dt dy/dt mag likelihood ra dec cos(dec)*dra/dt ddec/dt

#
"""
import string
import numpy as np
import logging
import os
import re
import sys
from astropy import units
from astropy.time import Time
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.units import Quantity
from mp_ephem.ephem import Observation
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

KEYS = string.digits + string.ascii_uppercase + string.ascii_lowercase


def year_to_letter(year):
    return chr(year - 2000 + ord('A'))


def index_to_key(index):
    return KEYS[index // 62] + KEYS[index % 62]


def key_to_index(key):
    return KEYS.index(key[0]) * 62 + KEYS.index(key[1])


def chip_to_key(chip):
    return KEYS[chip]


def key_to_chip(key):
    return KEYS.index(key)


@dataclass(frozen=False, kw_only=True, slots=True)
class KBModRecord:
    """
    A class to hold info about an object measured by
    the classy pipeline using KBMod
    """
    survey_field: str  # "Name of the CLASSY field"
    chip: int  # CCD number
    index: int  # "Index of the object in the field"
    mjd: float  # "MJD of the observation"
    x: Quantity  # "X position of the object on the CCD"
    y: float  # "Y position of the object on the CCD"
    dx: float  # "X velocity of the object on the CCD"
    dy: float  # "Y velocity of the object on the CCD"
    mag: (float, None)  # "Magnitude of the object"
    merr: (float, None)  # "Magnitude error of the object"
    likelihood: (float, None)  # "Likelihood of the object"
    ra: Quantity  # "Right ascension of the object"
    dec: Quantity  # "Declination of the object"
    dra: Quantity  # "rate of RA motion"
    ddec: Quantity  # "rate of DEC motion"
    provisional_name: str = field(init=False)
    coord: SkyCoord = field(init=False)
    date: Time = field(init=False)
    frame: str = field(init=False)
    observation: Observation = field(init=False)

    def __post_init__(self) -> None:
        self.date = Time(self.mjd, format='mjd')
        self.coord = SkyCoord(ra=self.ra, dec=self.dec, unit='deg', frame='icrs', obstime=self.date)
        year = year_to_letter(self.date.datetime.year)
        day = self.date.datetime.timetuple().tm_yday
        chip = chip_to_key(self.chip)
        index = index_to_key(self.index)
        self.provisional_name = f"{self.survey_field}{year}{day:03d}{chip}{index}"
        self.frame = f"{self.survey_field}{self.date.strftime('%y%m%d')}{self.chip:02d}"
        self.observation = Observation(provisional_name=self.provisional_name,
                                       frame=self.frame,
                                       survey_code='C',
                                       mag=self.mag,
                                       mag_err=self.merr,
                                       xpos=self.x.value,
                                       ypos=self.y,
                                       ra=self.ra * units.deg,
                                       dec=self.dec * units.deg,
                                       band='r',
                                       date=self.date,
                                       observatory_code=568,
                                       comment="",
                                       likelihood=self.likelihood)

    def offset(self, dt):
        """
        Return a new KBModRecord with the position offset by the velocity times dt
        """
        new_coord = self.coord.spherical_offsets_by(self.dra * dt.to(units.hour).value * units.arcsec,
                                                    self.ddec * dt.to(units.hour).value * units.arcsec)
        return KBModRecord(survey_field=self.survey_field,
                           chip=self.chip,
                           index=self.index,
                           mjd=self.mjd + dt.to(units.day).value,
                           x=self.x + self.dx * dt,
                           y=self.y + self.dy * dt.to(units.day).value,
                           dx=self.dx,
                           dy=self.dy,
                           mag=self.mag,
                           merr=self.merr,
                           likelihood=self.likelihood,
                           ra=new_coord.ra.degree,
                           dec=new_coord.dec.degree,
                           dra=self.dra,
                           ddec=self.ddec)

    def __str__(self):
        return f"{self.provisional_name} {self.date} " \
               f"{self.ra} {self.dec} {self.dra} {self.ddec} " \
               f"{self.mag} {self.merr} {self.likelihood}"


class KBModFileIterator(ABC):
    """
    Open an iterator over a KBMOD file, there are two types of KBMOD files, Discovery and Tracking
    """

    def __init__(self, survey_field, filename):
        self._next_line = None
        self._object_info = None
        self.filename = filename
        self.survey_field = survey_field
        self._fobj = None

    @property
    def fobj(self):
        if self._fobj is None:
            self._fobj = open(self.filename, 'r')
        return self._fobj

    @abstractmethod
    def get_measure(self) -> dict:
        pass

    @property
    def next_line(self) -> str:
        if self._next_line is None:
            self._next_line = self.fobj.readline()
            if self._next_line.strip().startswith("#"):
                self._next_line = None
                return self.next_line
        return self._next_line

    def __iter__(self):
        return self

    def __next__(self):
        """Return the next 'object' from the kbmod input file, or raise StopIteration"""
        m = self.get_measure()
        if m is None:
            raise StopIteration
        # gather all the observations of this source into a KBModRecord
        return KBModRecord(survey_field=self.survey_field, **m)


class TrackingFile(KBModFileIterator):
    """
    Class to loop over tacking observation file from lassy.
    """
    OBJ_MEASURE_COLUMNS = """
    chip
    index
    mjd
    x
    y
    dx
    dy
    mag
    likelihood
    ra
    dec
    dra
    ddec
    """.split()
    OBJ_MEASURE_COLUMNS_UNITS = """
    dimensionless
    dimensionless
    day
    pixel
    pixel
    pixel/day
    pixel/day
    magnitude
    dimensionless
    degree
    degree
    arcsec/day
    arcsec/day
    """.split()

    def get_measure(self):
        _mea = self.next_line.strip().split()
        if len(_mea) != len(TrackingFile.OBJ_MEASURE_COLUMNS):
            # Wrong number of records for a tracking observation
            logging.debug("Malformed line in KBMOD file: %s\n Expected %s" % (self.next_line,
                                                                              " ".join(
                                                                                  TrackingFile.OBJ_MEASURE_COLUMNS)))
            return None
        self._next_line = None
        m = {'merr': 0.99}
        for column in TrackingFile.OBJ_MEASURE_COLUMNS:
            v = _mea.pop(0)
            if "." in v:
                v = float(v)
            else:
                try:
                    v = int(v)
                except Exception as ex:
                    logging.debug(f"{column}: int({v}) -> {ex}")
            m[column] = v
        return m


class DiscoveryFile(KBModFileIterator):
    """
    Read in a Detection file.  Creates an iterator that returns sets of KBModRecords for the Discovery file
    """
    OBJ_START_LINE = re.compile(
        '\s*(?P<id>\d+)\s+(?P<dist>\d+(\.\d*)?)\s+(?P<mag>\d+(\.\d*)?)\s+(?P<visit>\d+)\s+(?P<chip>\d+)\s+(?P<ndet>\d+)\s*')
    OBJ_START_COLUMNS = "id dist mag visit chip ndet".split()
    OBJ_MEASURE_COLUMNS = "	x y dx dy mag mjd ra dec dra ddec".split()
    OBJ_MEASURE_COLUMN_UNITS = "pixel pixel pixel/hour pixle/hour mag day deg deg arcsec/hour arcsec/hour".split()

    def get_object_info(self):
        """Return the next 'object' from the kbmod input file, or return None if not found"""
        # Read the object info from the first line
        _obj = DiscoveryFile.OBJ_START_LINE.match(self.next_line)
        if _obj is not None:
            self._next_line = None  # We've read the first line, so reset the next line
            self._object_info = {}
            for column in _obj.groupdict().keys():
                value = _obj.group(column)
                op = int
                if "." in value:
                    op = float
                self._object_info[column] = op(value)

        return self._object_info

    def get_measure(self):
        object_info = self.get_object_info()
        if object_info is None:
            return None
        # Read the measurements of the object
        _mea = self.next_line.strip().split()
        if len(_mea) != len(DiscoveryFile.OBJ_MEASURE_COLUMNS):
            # Wrong number of records for a discovery observation
            logging.debug("Malformed line in KBMOD file: %s\n Expected %s" % (self.next_line,
                                                                              " ".join(
                                                                                  DiscoveryFile.OBJ_MEASURE_COLUMNS)))
            return None
        self._next_line = None  # We've read the line, so reset the next line
        m = {}
        m['chip'] = object_info['chip']
        m['index'] = object_info['id']
        m['merr'] = 0.99
        m['likelihood'] = -1
        for column in DiscoveryFile.OBJ_MEASURE_COLUMNS:
            m[column] = float(_mea.pop(0))
        return m

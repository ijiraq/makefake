"""
A group of objects that describe entities that the pipeline software will work on.
"""
import logging
import os
import shutil
import tempfile

from astropy import wcs
from astropy.io import fits
from astropy.table import Table
from cadcutils.exceptions import BadRequestException

from .params import *


class Observation(object):
    """
    An observation of a field.

    This is specific to CFHT MegaPrime observations and the package provides the path to the observation information.
    """

    def __init__(self, dataset_name, dbimages=None):
        if dbimages is None:
            dbimages = DBIMAGES
        self.dataset_name = dataset_name
        self.dbimages = dbimages

    @property
    def ccd_list(self):
        """
        A list of all the CCDs that this CFHT MegaPrime Exposure should have.
        :return:
        """
        if int(self.dataset_name) < 1785619:
            # Last exposures with 36 CCD MegaPrime
            return range(0, 36)
        return range(0, 40)

    def __str__(self):
        return "{}".format(self.dataset_name)


class Artifact(object):

    def __init__(self, observation, version=PROCESSED_VERSION,
                 ccd=None, subdir=None, ext=IMAGE_EXT, prefix=None):
        """
        The dataset_name comes from the observation that this artificat is part of.. Observtions can have many Artificats, for example
        the .fits image, the .psf.fits file, .mag file etc.

        Artifacts can be associated to a specific CCD that is part of the Mosaic of CCDs that make up the observation.

        :type version: str
        :type observation: Observation
        :type ccd: int
        :type subdir: str
        :type ext: str
        :type prefix: str
        :rtype: Artifact
        """
        self.observation = observation
        self.ccd = ccd
        self._subdir = subdir
        self._ext = ext
        self._version = version
        self._prefix = prefix
        self._hdulist = None

    @property
    def subdir(self):
        """
        Returns the name of the sub-directory where results are stored.

        By default the sub-directory is the name of the dataset.  So, if the data set is exposure 12345678 then the results will be
        stored in DBIMAGES/12345678  (standard dbimages data layout).  One can override this default when initializing the Artificat.

        :rtype: basestring
        """
        if self._subdir is None:
            self._subdir = self.observation.dataset_name
        return self._subdir

    @property
    def ext(self):
        """
        What is the extension of the file for this dataset.  For the fits images this would be .fits so that the filename becomee
        {dataset_name}.{ext}
        :rtype: basestring
        """
        if self._ext is None:
            self._ext = ""
        return self._ext

    @property
    def version(self):
        """
        The main image artificat may have a PROCESSSED 'p' or SCRAMBLED 's' or RAW 'o' version.  Version is the character after the
        datasets_name ... eg. 12345678p.fits has 'p' as the version.
        :rtype: basestring
        """

        if self._version is None:
            self._version = ""
        return self._version

    @property
    def prefix(self) -> str:
        """
        The prefix is nominally 'fk' for images that have artificial sources added and left blank for others.

        """
        if self._prefix is None:
            self._prefix = ""
        return self._prefix

    @property
    def uri(self) -> str:
        """
        Build the uri for an CLASSY image stored in the dbimages containerNode.

        depends on other elements defined for this Artifact.

        dataset_name: CFHT exposure number
        ccd: CCD in the mosaic [0-35]
        version: one of p,s,o etc.
        prefix:
        dbimages: dbimages containerNode.
        """
        uri = "{}/{}".format(self.observation.dbimages, self.subdir)

        if self.ccd is None:
            return "{}/{}{}{}.{}".format(uri, self.prefix, self.observation, self.version, self.ext)

        return "{}/ccd{:02d}/{}{}{}{:02d}.{}".format(uri, int(self.ccd),
                                                     self.prefix, self.observation, self.version,
                                                     self.ccd, self.ext)

    def link(self):
        """Create a link from the artifact in dbimages to the current directory."""
        if not os.access(self.filename, os.F_OK):
            logging.info("Retrieving {} from VOSpace".format(self.uri))
            return os.link(self.uri, self.filename)
        return 0

    @property
    def filename(self):
        return os.path.basename(self.uri)

    def put(self):
        """Put the artifact to the dbimages directory."""
        # first ensure the path exists
        logging.info("Checking that path {} exists".format(self.uri))
        os.makedirs(self.uri)
        logging.info("Copying {} to {}".format(self.filename, self.uri))
        return shutil.copyfile(self.filename, self.uri)

    def delete(self):
        """Delete a file from VOSpace"""
        return os.unlinkn(self.uri)


class FitsArtifact(Artifact):

    @property
    def hdulist(self):
        if self._hdulist is not None:
            return self._hdulist
        if not os.access(self.filename, os.R_OK):
            self.get()
        self._hdulist = fits.open(self.filename)
        return self._hdulist

    @hdulist.setter
    def hdulist(self, hdulist):
        self._hdulist = hdulist


class FitsTable(FitsArtifact):

    def __init__(self, *args, **kwargs):
        super(FitsTable, self).__init__(*args, **kwargs)
        self._table = None

    @property
    def table(self):
        """

        :return: Table object built from this FitsArtifact
        :rtype: Table
        """
        if self._table is None:
            if not os.access(self.filename, os.R_OK):
                self.get()
            self._table = Table.read(self.filename)
        return self._table

    @table.setter
    def table(self, table):
        self._table = table

    def write(self):
        """
        Write the current data in the table to disk.
        """
        if self.table.meta['EXTNAME'] in self.hdulist:
            del (self.hdulist[self.table.meta['EXTNAME']])
        self.hdulist.append(fits.table_to_hdu(self.table))
        self.hdulist.writeto(self.filename, clobber=True)


class Image(FitsArtifact):
    """
    An image artifact is the main artifact of an observation.  This artifact refers to a sepcific CCD in the MOSAIC.
    """
    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(Image, self).__init__(*args, **kwargs)
        self._ccd = None
        self.ccd = kwargs.get('ccd', None)
        self._header = None
        self._wcs = None
        self._flat_field_name = None
        self._flat_field = None
        self._footprint = None
        self._polygon = None
        self._ext = IMAGE_EXT

    @property
    def ext(self) -> str:
        return self._ext

    @property
    def ccd(self) -> int:
        return self._ccd

    @ccd.setter
    def ccd(self, ccd):
        self._wcs = self._polygon = self._header = None
        self._ccd = ccd

    @property
    def filename(self) -> str:
        if self.ccd is None:
            return os.path.basename(self.uri)
        return "{}{}{}{:02d}.{}".format(self.prefix,
                                          self.observation,
                                          self.version,
                                          self.ccd,
                                          self.ext)

    @property
    def header(self) -> fits.Header:
        """
        :return:         The Header of the FITS Extension hold this image.
        :rtype: fits.Header
        """
        _header = None
        filename = self.filename
        if not os.access(filename, os.R_OK):
            filename = self.uri
        if not os.access(filename, os.R_OK):
            raise FileNotFoundError(filename)
        with fits.open(filename) as hdulist:
            _header = hdulist[0].header
        return _header

    @property
    def wcs(self) -> wcs.WCS:
        if self._wcs is None:
            if self.ccd is None:
                raise ValueError("No CCD supplied so don't know which WCS to return")
            self._wcs = wcs.WCS(self.header)
        return self._wcs

    @property
    def footprint(self):
        return self.wcs.calc_footprint()

    @property
    def uri(self):
        """
        Build the uri for an OSSOS image stored in the dbimages
        containerNode.

        :rtype : basestring
        dataset_name: CFHT exposure number
        ccd: CCD in the mosaic [0-35]
        version: one of p,s,o etc.
        dbimages: dbimages containerNode.
        """
        uri = "{}/{}".format(self.observation.dbimages, self.subdir)

        if self.ccd is None:
            return "{}/{}{}{}{}".format(uri, self.prefix, self.observation, self.version, self.ext)

        return "{}/{}{}{}{}[{}]".format(uri,
                                        self.prefix, self.observation, self.version, self.ext,
                                        self.ccd + 1)

    @property
    def flat_field(self):
        """

        :rtype: Image
        """
        if self._flat_field is None:
            self._flat_field = Image(Observation(self.flat_field_name, dbimages=FLATS_VOSPACE),
                                     subdir="",
                                     ext=".fits",
                                     version="",
                                     ccd=self.ccd)
        return self._flat_field

    @property
    def flat_field_name(self) -> str:
        """
        Get the name of the flat field file used from the image header.
        :return:
        """
        if self._flat_field_name is not None:
            return self._flat_field_name
        if self.ccd is None:
            raise ValueError("Getting the flat_field_name for the entire MOSAIC is not well defined")
        self._flat_field_name = self.header.get('FLAT', None)
        if self._flat_field_name is None:
            self._flat_field_name = "weight.fits"
        self._flat_field_name = self._flat_field_name.rstrip(".fits")
        return self._flat_field_name

    @property
    def fwhm(self):
        uri = Artifact(self.observation, ccd=self.ccd, version=self.version, ext='fwhm', prefix=self.prefix).uri
        filename = os.path.basename(uri)
        copy(uri, filename)
        return open(filename).read()

    @property
    def zeropoint(self):
        """
        r.MP9602 = r_SDSS - 0.087*(g_SDSS - r_SDSS)

        For KBOs g_SDSS - r_SDSS ~ 0.8 => r.MP9602 = r_SDSS - 0.07
        or
        r_SDSS = r.MP9602 + 0.07 .. ZP is in r.MP9602

        with r.MP9602 = -2.5*log10(AUD) + PHOTZP   (there is no airmass of color term as this is a filter ZP calibrated in-frame)
        :return:
        """
        return float(self.header.get(ZEROPOINT_KEYWORD, 30.0))


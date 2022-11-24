"""
Script to build an ASTRORES formated Ephemeris file for upload to CFHT PH2.
"""
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy.table import Table
from astropy import units
import sys

if len(sys.argv) != 3:
    sys.stderr.write(f"Usage: {__file__} SL_foramted_ephem_file output_astrores_xml_filename\n")
    sys.exit(-1)

input_ephem = Table.read(sys.argv[1], format='ascii.no_header', guess=False)
output_xml = sys.argv[2]

with open(output_xml, 'w') as fobj:
    fobj.write("""<?xml version = "1.0"?>
<!DOCTYPE ASTRO SYSTEM "http://vizier.u-strasbg.fr/xml/astrores.dtd">
<ASTRO ID="v0.8" xmlns:ASTRO="http://vizier.u-strasbg.fr/doc/astrores.htx">
  <TABLE ID="Table">
    <NAME>Ephemeris</NAME>
    <TITLE>Ephemeris for CFHT QSO</TITLE>
    <!-- Definition of each field -->
    <FIELD name="DATE_UTC"  datatype="A" width="19" format="YYYY-MM-DD hh:mm:ss"> 
        <DESCRIPTION>UTC Date</DESCRIPTION>
    </FIELD>	
    <FIELD name="RA_J2000"  datatype="A" width="11" unit="h"   format="RAh:RAm:RAs">
        <DESCRIPTION>Right ascension of target</DESCRIPTION>
    </FIELD>
    <FIELD name="DEC_J2000" datatype="A" width="11" unit="deg" format="DEd:DEm:DEs">
        <DESCRIPTION>Declination of target</DESCRIPTION>
    </FIELD>
    <!-- Data table -->
<DATA><CSV headlines="4" colsep="|">
<![CDATA[
DATE_UTC           |RA_J2000   |DEC_J2000  |
YYYY-MM-DD hh:mm:ss|hh:mm:ss.ss|+dd:mm:ss.s|
1234567890123456789|12345678901|12345678901|
-------------------|-----------|-----------|\n""")
    for row in input_ephem:
        year = int(row['col1'])
        month = int(row['col2'])
        day = int(row['col3'])
        ra = float(row['col4'])
        de = float(row['col5'])
        date = Time(f"{year:4d}-{month:02d}-{day:02d}T10:00:00")
        pos = SkyCoord(ra, de, unit='deg', obstime=date)
        sra = pos.ra.to_string(units.hour, sep=":", precision=2, pad=True)
        sdec = pos.dec.to_string(units.degree, sep=":", precision=1, pad=True, alwayssign=True)
        sdate = str(pos.obstime.replicate(format('iso')))[0:19]
        fobj.write(f"{sdate:19s}|{sra:11s}|{sdec:11s}|\n")


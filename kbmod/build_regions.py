from astropy.coordinates import SkyCoord
from astropy.table import Table
import sys
import astropy.units as u
from regions import CircleSkyRegion, Regions

t = Table.read(sys.argv[1], format='ascii')

regions = Regions([])
visual={'default_style': 'ds9', 'facecolor': 'green', 'edgecolor': 'green'}
coords = SkyCoord(t['ra'], t['dec'], unit='deg', frame='fk5')
for coord in coords:
    region = CircleSkyRegion(coord, radius=5/3600. * u.deg, visual=visual)
    regions.append(region)
regions.serialize(format='ds9', precision=8)
regions.write('my_region.ds9', format='ds9', overwrite=True)

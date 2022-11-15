from astropy.io import fits
import sys
print(fits.open(sys.argv[1])[0].header.get(sys.argv[2],None))

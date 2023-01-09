from astropy.io import fits
import glob
import argparse
import os
import logging

def grid(filename, width=100, height=100, padding=0):
    """
    break fits ImageHDUs in filename into grid of sub-images of size width-x-height.  Correct the WCS 
    """
    logging.info(f"Gridding {filename}")
    with fits.open(filename) as hdulist:
        naxis1=hdulist[1].header['NAXIS1']
        naxis2=hdulist[1].header['NAXIS2']
        chunk=0
        for x1 in range(0, naxis1, width):
            x2 = min(x1+width, naxis1-1)
            for y1 in range(0, naxis2, height):
                y2 = min(y1+height, naxis2-1)
                logging.debug(f"chunk: [{x1}:{x2},{y1}:{y2}]")
                new_hdulist = fits.HDUList()
                hdu = hdulist[0]
                new_hdulist.append(fits.PrimaryHDU(data=hdu.data, header=hdu.header))
                for hdu in hdulist[1:]:
                    logging.debug(f"working with hdu: {hdu} {hdu.header['EXTTYPE']} {hdu.header['NAXIS']} {hdu.header['NAXIS1']},{hdu.header['NAXIS2']}")
                    if not isinstance(hdu, fits.ImageHDU):
                        continue
                    new_hdulist.append(fits.ImageHDU(data=hdu.data[y1:y2, x1:x2], header=hdu.header))
                    new_hdulist[-1].header['CRIPXI1'] = hdu.header['CRPIX1'] - x1
                    new_hdulist[-1].header['CRIPIX2'] = hdu.header['CRPIX2'] - y2
                dirname = f"chunk_{chunk:05d}"
                if not os.access(dirname, os.F_OK):
                    os.mkdir(dirname)
                out_filename = os.path.basename(filename.replace('.fits',f'-{x1:04d}-{x2:04d}-{y1:04d}-{y2:04d}.fits'))
                out_filename = os.path.join(dirname, out_filename)
                logging.debug(f"Writing chunk to {out_filename}")
                new_hdulist.writeto(out_filename)
                chunk += 1
                return


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='+', help="List of files to gird")
    parser.add_argument('--log-level', choices=['INFO', 'DEBUG', 'ERROR'], default='ERROR', help="Logging level")
    parser.add_argument('--width', type=int, default=100, help="width of chunk")
    parser.add_argument('--height', type=int, default=100, help="height of chunk")
    
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))
    for filename in args.filenames:
        grid(filename, width=args.width, height=args.height)


if __name__ == '__main__':
    main()

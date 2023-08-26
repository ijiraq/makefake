import numpy as np
import sys, os, glob, pickle, gc
import argparse
import logging
from  astropy import time
from astropy.io import fits

def split_images(img_path: str, split_ind: int, n_splits: int = 4, overlap:int = 150,
                 split_img_path: str = None, max_num_files: int = 123, filename_pattern: str = "DIFFEXP*.fits"):
    """
    For each FITS image in img_path that matches filename_pattern extract the split_ind chunk of the image where
    the image will be divided into n_splits y-axis chunks. Preserves the WCS

    :param str img_path: directory containing files matching filename_pattern
    :param int split_ind: which index or n_splits to take from image
    :param int n_splits: Number of splits to make, default is 4
    :param int overlap: number of pixels of overlaps between chunks
    :param str split_img_path: filesystem location to store the split images to
    :param int max_num_files: maximum number of files to work on
    :param str filename_pattern: the glob expression used to select files in img_path directory

    
    """
    if n_splits==1:
        raise ValueError(f"Number of splits set to {n_splits} which has no effect?")

    files = glob.glob(f'{img_path}/DIFFEXP*.fits')
    files.sort()
    logging.info(f'Splitting image into {split_ind+1} of {n_splits} sections.')

    if split_img_path is None:
        full_path=f'{img_path}/splitims_{split_ind}_{n_splits}'
    else:
        full_path = f'{split_img_path}/splitims_{split_ind}_{n_splits}'

    logging.info(f"Storing resulting split images to {full_path}")
    os.makedirs(full_path, exist_ok=True)
        
    for f in files[:max_num_files]:
        outname = f"{full_path}/{f.split('/')[-1]}"
        han = fits.open(f)
        for ii in range(1,4): #loop over the HDU extensions
            d = han[ii].data

            (A,B) = d.shape
            split = [max(0, int(A/n_splits)*split_ind-overlap),
                         min(A, int(A/n_splits)*(split_ind+1)+overlap)]

            han[ii].data = d[split[0]:split[1], :]

            han[ii].header['CRPIX2'] = han[1].header['CRPIX2'] - split[0]
        logging.debug(f"Writing split for {f} to {outname}")
        han.writeto(outname, overwrite=True)
        han.close()
    return full_path


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--n-splits', default=4, help="How many chunks should the images be split into?", type=int)
    parser.add_argument('--split-index', default=None, help="Only cutout out this split-index of n-splits chunks", type=int)
    parser.add_argument('--overlap', default=150, help="How many pixels of overlap between chunks?", type=int)
    parser.add_argument('diff_dir', help="Name of the directory holding the difference images to be split")
    parser.add_argument('split_dir', help='Base name of the directory to distribute split images into, need not previously exist',
                        default='/scratch/kbmod')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARN', 'ERROR'], default='ERROR')
    args = parser.parse_args()
    
    logging.basicConfig(level=getattr(logging, args.log_level))

    logging.debug(f"Called with {args}")
    im_filepath=args.diff_dir
    split_img_path=args.split_dir
    logging.info(f"Splitting DIFFEXP*.fits files in {im_filepath} into {args.n_splits} chunks stored in {split_img_path}")
    indices = [args.split_index] if args.split_index is not None else range(args.n_splits)
    logging.debug(f"Splitting indices {indices}")
    
    for i in indices:
        split_images(im_filepath, i, n_splits=args.n_splits, overlap=args.overlap, split_img_path=split_img_path)

import numpy as np
import sys, os, glob, pickle, gc
from  astropy import time
from astropy.io import fits

def create_times_file(img_path, file_fn):
    files = glob.glob(f'{img_path}/DIFFEXP*fits')
    files.sort()

    outhan = open(file_fn, 'w+')
    for ii, fn in enumerate(files):
        with fits.open(fn) as han:
            t = time.Time(han[0].header['DATE-AVG'], format='isot')
        n = fn.split('DIFFEXP-')[1].split('-')[0]
        print('{} {:12.6f}'.format(int(float(n)),t.mjd),file=outhan)
    outhan.close()


def split_images(img_path, split_ind, n_splits=4, overlap=150, split_img_path=None, maxNumFiles=123):
    files = glob.glob(f'{img_path}/DIFFEXP*fits')
    files.sort()
    #print(files)
    #print(f'{img_path}/DIFFEXP*fits')
    print(f'Splitting image into {split_ind+1} of {n_splits} sections.')

    if split_img_path is None:
        full_path=f'{img_path}/splitims_{split_ind}_{n_splits}'
    else:
        full_path = f'{split_img_path}/splitims_{split_ind}_{n_splits}'
    os.system(f'mkdir {full_path}')
        
    for f in files[:maxNumFiles]:
        outname = full_path+'/'+f.split('/')[-1]
        if n_splits==1:
            os.system(f'cp {f} {outname}')
            continue
        han = fits.open(f)
        for ii in range(1,4): #loop over the HDU extensions
            d = han[ii].data

            (A,B) = d.shape
            split = [max(0, int(A/n_splits)*split_ind-overlap),
                         min(A, int(A/n_splits)*(split_ind+1)+overlap)]

            han[ii].data = d[split[0]:split[1], :]

        han[1].header['CRPIX2'] = han[1].header['CRPIX2'] - split[0]

        han.writeto(outname, overwrite=True)
        han.close()
    return full_path


def clear_split_images(img_path, split_ind, n_splits=4):
    os.system(f'rm -r {img_path}/splitims_{split_ind}_{n_splits}')
    return


if __name__ == "__main__":
    import sys
    
    n_splits = 1
    visit = '03072'
    chipNum = '044'
    project = 'NewHorizons'
    
    #n_splits = 3
    #visit = '2022-08-22'
    #chipNum = '02'
    #project = 'classy'

    do_ind = -1
    if len(sys.argv)>1:
        chipNum = str(sys.argv[1]).zfill(3)
        visit = str(sys.argv[2])
        if '-0' in sys.argv:
            do_ind = 0
        elif '-1' in sys.argv:
            do_ind = 1
        elif '-2' in sys.argv:
            do_ind = 2
        elif '-3' in sys.argv:
            do_ind = 3
        elif '-4' in sys.argv:
            do_ind = 4
            
    im_filepath= f"/arc/projects/{project}/DATA/warps/{visit}/{str(chipNum).zfill(3)}"
    if project=='classy':
        im_filepath= f"/arc/projects/{project}/WesSandbox/warps/{visit}/{str(chipNum).zfill(2)}"
    split_img_path = f'/scratch/fraserw/warps/{visit}/{chipNum}'
    print(im_filepath)
    
    create_times_file(im_filepath, f'/arc/projects/{project}/DATA/kbmod_times_files/{visit}/times_c{str(chipNum).zfill(3)}.dat')
    #exit()
    if not os.path.isdir(split_img_path):
        os.system(f'mkdir -p {split_img_path}')

    if do_ind == -1:
        for i in range(n_splits):
            split_images(im_filepath, i, n_splits=n_splits, overlap=150, split_img_path=split_img_path)
    else:
        split_images(im_filepath, do_ind, n_splits=n_splits, overlap=150, split_img_path=split_img_path)

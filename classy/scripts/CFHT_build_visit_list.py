from astropy.io import fits
import glob, os, sys, numpy as np
import argparse

frac_ims_for_template = 0.3

date_obs = '2022-08-22'
if len(sys.argv)>1:
    date_obs = sys.argv[1]

visit_lists_dir = '/arc/projects/classy/WesSandbox/visitLists'
db_images_dir = '/arc/projects/classy/dbimages'
db_images = []
with open(f'{db_images_dir}/image.list') as han:
    data = han.readlines()
for i in range(len(data)):
    s = data[i].split()
    im = s[0]
    d = s[1]
    if date_obs == d:
        db_images.append(im)

im_iqs = []
for i, im in enumerate(db_images):
    image_fn = im.split('/')[0]
    psf_fn = f'{db_images_dir}/{image_fn}/ccd22/{image_fn}p22.psf.fits'
    with fits.open(psf_fn) as han:
        fwhm = han[0].header['FWHM']
    im_iqs.append(fwhm)

im_iqs = np.array(im_iqs)
db_images = np.array(db_images)

args = np.argsort(im_iqs)
max_i = int(len(args)*frac_ims_for_template)

try:
    os.mkdir(f'{visit_lists_dir}/{date_obs}')
except:
    pass

with open(f'{visit_lists_dir}/{date_obs}/{date_obs}_visit_list.txt', 'w+') as han:
    for i, im in enumerate(db_images):
        print(im.split('/')[0], file=han)
with open(f'{visit_lists_dir}/{date_obs}/{date_obs}_template_visit_list.txt', 'w+') as han:
    for i, im in enumerate(db_images[args[:max_i]]):
        print(im.split('/')[0], file=han)

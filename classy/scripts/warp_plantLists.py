from astropy import wcs as WCS
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u
import glob, sys
import numpy as np


chip = '00'
visit = '2022-08-22'
programID = '22BP34'
field = 'AS2'
filt = 'r2'
if len(sys.argv)>1:
    chip = sys.argv[1].zfill(2)
    visit = sys.argv[2]
    programID = sys.argv[3]
    field = sys.argv[4]
    filt = sys.argv[5]
    
warps_path = f'/arc/projects/classy/WesSandbox/warps/{visit}/{chip}'
warps = glob.glob(warps_path+'/DIFF*fits')
warps.sort()


butler_path = f'/arc/projects/classy/WesSandbox/rerun/processCcdOutputs/calexp/{programID}/{field}/{visit}/{filt}/'

plant_ims_dir = '/arc/projects/classy/dbimages/'
plantLists = []
for i,fn in enumerate(warps):
    im_n = fn.split('DIFFEXP-')[1].split('-')[0]

    l = glob.glob(f'{plant_ims_dir}/{im_n}/ccd{chip}/{im_n}*plantList')
    plantLists.append(l[0])
plantLists.sort()

if len(warps)==0:
    print('Found no warps at the provided path. Exiting.')
    exit()


with fits.open(warps[0]) as han:
    header = han[1].header
    wcs = WCS.WCS(header)
ref_im_num = warps[0].split('DIFFEXP-')[1].split('-')[1][:7]

for i in plantLists:
    s = i.split('/')[-1]
    print(s)
    new_plant_fn = s.replace(f'.plantList', f'-{ref_im_num}p{chip}.plantList')


    with open(i) as han:
        data = han.readlines()

    try:
        ra_dec = []
        for j in range(1, len(data)):
            s = data[j].split()
            ra_dec.append([float(s[1]), float(s[2])])
        ra_dec = np.array(ra_dec)
        astro_coords = SkyCoord(ra_dec[:, 0]*u.deg, ra_dec[:, 1]*u.deg)
        coords = wcs.world_to_pixel(astro_coords)
    except:
        continue

    #print(coords)
    #print(wcs.all_world2pix(ra_dec, 0))
    #exit()

    with open(f'{warps_path}/{new_plant_fn}', 'w+') as outhan:
        print(data[0], end='', file=outhan)
        for j in range(1,len(data)):
            s = data[j].split()
            s[3] = '{:7.2f}'.format(coords[0][j-1])
            s[4] = '{:7.2f}'.format(coords[1][j-1])
            print(' '.join(s), file=outhan)


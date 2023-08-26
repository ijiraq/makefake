from lsst.afw import image
from lsst.afw.math.warper import Warper
import glob, sys, os

warper = Warper('lanczos4')


but_path = '/arc/projects/classy/WesSandbox/CFHT_DPS'
visit = '2022-08-22'
chip = '00'
field='AS2'
programID='22BP34'
filt='r2'
refexp=2778855
out_path = f'/arc/projects/classy/WesSandbox/warps'
if len(sys.argv)>1:
    but_path = sys.argv[1]
    visit = sys.argv[2]
    chip = sys.argv[3]
    field=sys.argv[4]
    programID=sys.argv[5]
    filt=sys.argv[6]
    refexp=sys.argv[7]
    out_path = sys.argv[8]

ind = None
if len(sys.argv)==10:
    ind = int(float(sys.argv[9]))
              
ref_exp_fn = f'{but_path}/rerun/diff_warpCompare_{chip}/deepDiff/{programID}/{field}/{visit}/{filt}/DIFFEXP-{refexp}-{chip}.fits'
ref_exp = image.ExposureF(ref_exp_fn)
ref_wcs = ref_exp.getWcs()
ref_bbox = ref_exp.getBBox()



diff_files = glob.glob(f'{but_path}/rerun/diff_warpCompare_{chip}/deepDiff/{programID}/{field}/{visit}/{filt}/DIFFEXP-???????-{chip}.fits')
diff_files.sort()

try:
    os.makedirs(f'{out_path}/{visit}/{chip}')
except:
    pass

if ind is None:
    a, b = 0, len(diff_files)
else:
    a, b = ind, ind+1

for i, fn in enumerate(diff_files[a:b]):
    print(i+1, len(diff_files), fn)
    im = fn.split('/')[-1]
    out_fn = out_path+f'/{visit}/{chip}/'+im.replace(f'{chip}.fits',f'{refexp}-{chip}.fits')

    exp = image.ExposureF(fn)
    exp_vis = fn.split('DIFFEXP-')[1].split('-')[0]

    warpedExp = warper.warpExposure(ref_wcs, exp, destBBox=ref_bbox)
    warpedExp.writeFits(out_fn)

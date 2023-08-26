import sys, os, glob

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

try:
    os.makedirs(f'{out_path}/{visit}/{chip}')
except:
    pass

diff_files = glob.glob(f'{but_path}/rerun/diff_warpCompare_{chip}/deepDiff/{programID}/{field}/{visit}/{filt}/DIFFEXP-???????-{chip}.fits')
diff_files.sort()


for i in range(len(diff_files)):
    comm = f'python stack_scripts_cfht/singleChip/run_diff_warp.py {but_path} {visit} {chip} {field} {programID} {filt} {refexp} {out_path} {i}'
    print(comm)
    

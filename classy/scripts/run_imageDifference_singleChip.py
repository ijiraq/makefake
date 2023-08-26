#! /usr/bin/env python
import os
import sys
from pathlib import Path
import logging
import argparse
from glob import glob
import re

command="imageDifference.py"

parser = argparse.ArgumentParser()
parser.add_argument('basedir', help="Base data directory, contains the 'rerun' dir")
parser.add_argument('pointing', help="Which pointing are we doing? (eg. 03093)")
parser.add_argument('--chip', help="Output directory to store differeince images", default=44)
parser.add_argument('--diff', help="Output directory to store differeince images", default="diff_warpCompare")
parser.add_argument('--coadd', help="rerun that has the template images", default='{pointing}_warpCompare')
parser.add_argument('--plant', help="reurn with images to be differenced", default='processCcdOutputs')
parser.add_argument('--log-level', choices=['INFO', 'DEBUG', 'ERROR', 'WARNING'], default="INFO")
parser.add_argument('--filter', help="What filter do you want to create diffs for? (eg. r2 or gri)")
parser.add_argument('--programID', help='What program ID are the observations from? (eg. %default)', default='22BP34')
parser.add_argument('--field', help='What field name are the observations from? (eg. %default).', default='AS2')
args = parser.parse_args()


logging.basicConfig(level=getattr(logging, args.log_level), format='# %(levelname)s:%(module)s:%(lineno)d:%(message)s')

chip = args.chip.zfill(2)
pointing = args.pointing
basedir = args.basedir.format(**locals())
coadd = args.coadd.format(**locals())+'_'+chip
plant = args.plant.format(**locals())
diff = args.diff.format(**locals())+'_'+chip
programID = args.programID
field = args.field
filter = args.filter.format(**locals()) #'r2'

basename = os.path.splitext(command)[0]
config = f"/arc/projects/classy/lsst_cfht_testing/configs/{basename}_config.py"
if not os.access(config, os.R_OK):
    raise FileNotFoundError(config)

script_dir = f"logs/{pointing}/{basename}/inputs"
Path(script_dir).mkdir(parents=True, exist_ok=True)
log_dir = f"logs/{pointing}/{basename}/logs"
Path(log_dir).mkdir(parents=True, exist_ok=True)

# And placed into diff
dest_dir = f"{basedir}/rerun/{diff}/deepDiff/{pointing}/{filter}"
source_dir = f"{basedir}/rerun/{plant}/calexp/{programID}/{field}/{pointing}/{filter}"#/corr"
#print(source_dir)


for ccd in range(int(chip), int(chip)+1):
    chip=f"{ccd:02d}"
    for plant_file in glob(f"{source_dir}/calexp-*-{chip}.*"):
        logging.debug(f"# Got plant_file {plant_file}")
        visit = re.search(r"-(?P<visit>\d{6,7})-", plant_file).group(1)
        diff_filename = f"DIFFEXP-{visit}-{chip}.fits"
        if os.access(f"{dest_dir}/{diff_filename}", os.F_OK):
            continue
        logfile = f"{log_dir}/{visit}_{ccd}.txt"
        filename = f"{script_dir}/{visit}_{ccd}.txt"
        logging.debug(f"# {dest_dir}/{diff_filename} RUNNING")
        with open(filename, 'w') as fobj:
            fobj.write(f"--rerun {coadd}:{diff} \n")
            fobj.write(f"--id visit={visit} ccd={ccd} \n")
            fobj.write(f"--clobber-config --configfile {config}\n")
            #print(f"--rerun {coadd}:{diff} \n")
            #print(f"--id visit={visit} ccd={chip} \n")
            #print(f"--clobber-config --configfile {config}\n")
        sys.stdout.write(f"{command} {basedir} @{filename} > {logfile} 2>&1\n")


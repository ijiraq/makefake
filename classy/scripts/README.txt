#!/bin/bash

###
# Wes note: cd to /arc/projects/classy. Set basedir=/arc/projects/classy/lsst_cfht_testing/CFHT, pointing=2019-07-01 and pointingdir=calexp/19AC24/SatEastDis/${pointing} for example
###

# Short README (which you can run as a script if you are really
# looking for a single command) on processing the Planted images from
# the New Horizons Subaru HSC data processed through LSST Pipeline v19

# TLDR;

# Start an lsst container
# Run the following in an lsst terminal in arcade or call this file as
# cd ~/git && setup obs_cfht -t fraserw

cd /arc/projects/classy/WesSandbox
basedir=/arc/projects/classy/WesSandbox/CFHT_DPS
pointing=$1 && shift
chip=$1 && shift
filter=$1 && shift
field=$1 && shift
programID=$1 && shift
refexp=$1 && shift

#python stack_scripts_cfht/CFHT_build_visit_list.py ${field}

echo INFO: Making discrete skymap
bash stack_scripts_cfht/singleChip/run_makeDiscreteSkyMap_on_visit_list.sh ${basedir} ${pointing} ${chip}

echo INFO: Making discrete temp exp
bash stack_scripts_cfht/singleChip/run_makeCoaddTempExp_on_visit_list.sh ${basedir} ${pointing}  ${chip} ${filter} 0 0 | parallel

echo INFO: Assembling coadds
bash stack_scripts_cfht/singleChip/run_assembleCoadd_nowarp.sh ${basedir} ${pointing} ${chip} ${filter} 0,0 | parallel

echo INFO: Differencing
python stack_scripts_cfht/singleChip/run_imageDifference_singleChip.py ${basedir} ${pointing} --chip ${chip} --filter ${filter} --diff diff_warpCompare --coadd ${pointing}_warpCompare --field ${field} --programID ${programID}  | parallel

#python stack_scripts_cfht/singleChip/run_diff_warp.py ${basedir} ${pointing} ${chip} ${field} ${programID} ${filter} ${refexp} /arc/projects/classy/WesSandbox/warps

# parallel version of warping
echo INFO: Warping
python stack_scripts_cfht/singleChip/diff_warp_parallel.py ${basedir} ${pointing} ${chip} ${field} ${programID} ${filter} ${refexp} /arc/projects/classy/WesSandbox/warps | parallel

python stack_scripts_cfht/singleChip/warp_plantLists.py ${chip} ${pointing} ${programID} ${field} ${filter}
exit 0
 

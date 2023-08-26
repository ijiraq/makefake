
chip=$1
pointing=$2
basedir=$3


bash stack_scripts/singleChip/run_makeDiscreteSkyMap_on_visit_list.sh ${basedir} ${pointing} ${chip}
bash stack_scripts/singleChip/run_makeCoaddTempExp_on_visit_list.sh ${basedir} ${pointing}  ${chip} | parallel
bash stack_scripts/singleChip/run_assembleCoadd_nowarp.sh ${basedir} ${pointing} ${chip} | parallel
python stack_scripts/singleChip/run_imageDifference_singleChip.py ${basedir} ${pointing} --diff diff_noWarpCompare --coadd ${pointing}_nowarpCompare --chip ${chip} | parallel

#!/bin/bash
# loop over a set of exposure numbers launching the mask making tasks in DBIMAGES for each
CMD=$(basename ${BASH_SOURCE[0]})
SRCDIR=$(dirname ${BASH_SOURCE[0]})
NOPTS=2
TYPE="interp"
VERSION="p"
PREFIX="fk"
USAGE="${CMD} expoure_list ccd

For each expousre number in the list find the ${TYPE}_${PREFIX} image for the given CCD in dbimages and run makeMask on that image
"
. ${SRCDIR}/utils.sh
expousre_list=$1 && shift
ccd=$1 && shift
cwd=$(pwd)

while IFS="" read expnum || [[ -n ${expnum} ]]
do
    name="mask-${expnum}"
    imagename=$(get_image_filename ${TYPE} ${PREFIX} ${expnum} ${VERSION} ${ccd})
    logmsg DEBUG "expnum: ${expnum} ccd: ${ccd}"
    directory=$(get_dbimages_directory ${expnum} ${ccd})
    cd $directory || logmsg ERROR "Cannot change to directory ${directory}"
    if [ -f "${name}.OK" ]
    then
	logmsg WARNING "Mask already succeed for ${image}"
	continue
    fi
    logmsg INFO "launching mask on ${imagename} in ${directory}"
    sk_launch.sh uvickbos/pycharm:0.1 mask-${expnum} /arc/home/jkavelaars/classy-pipeline/venv/bin/python /arc/home/jkavelaars/classy-pipeline/isis/makeMask.py ${imagename}
done < ${expousre_list}



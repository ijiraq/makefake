#!/bin/bash
# loop over a set of exposure numbers launching the mask making tasks in DBIMAGES for each
CMD="$(basename "${BASH_SOURCE[0]}")"
SRCDIR="$(dirname "${BASH_SOURCE[0]}")"
export NOPTS=2
TYPE="interp"
VERSION="p"
PREFIX="fk"
export USAGE="${CMD} exposure_list ccd

For each exposure number in the list find the ${TYPE}_${PREFIX} image for the given CCD in dbimages and run makeMask on that image
"
. "${SRCDIR}/utils.sh"
exposure_list=$1 && shift
ccd=$1 && shift

while IFS="" read -r expnum || [[ -n ${expnum} ]]
do
    name="mask-${expnum}-${ccd}"
    image_name="$(get_image_filename ${TYPE} ${PREFIX} "${expnum}" ${VERSION} "${ccd}")"
    logmsg DEBUG "expnum: ${expnum} ccd: ${ccd}"
    directory="$(get_dbimages_directory "${expnum}" "${ccd}")"
    cd "$directory" || logmsg ERROR "Cannot change to directory ${directory}"
    logmsg INFO "launching mask on ${image_name} in ${directory}"
    sk_launch.sh uvickbos/pycharm:0.1 "${name}" \
    /arc/home/jkavelaars/classy-pipeline/venv/bin/python "${SRCDIR}/makeMask.py" "${image_name}"
done < "${exposure_list}"

#!/bin/bash
# loop over a set of exposure numbers launching the imageDifference task with correct inputs
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
export NOPTS=2
DIFF="conv"
INTERP="interp"
MASK="mask"
export USAGE="${CMD} exposure_list ccd

Build a DIFFEXP file from inputs found in the dbimages/expnum/ccd/ directory
"

. "${SRCDIR}/utils.sh"

exposure_list=$1 && shift
ccd=$1 && shift

while IFS="" read -r expnum || [[ -n ${expnum} ]]
do
    img_dir="$(realpath "$(get_dbimages_directory "${expnum}" "${ccd}")")"
    cd "${img_dir}" || logmsg ERROR "Cannot change to ${img_dir} to run difference" $?
    primary="$(get_image_filename "" "${PREFIX}" "${expnum}" "${VERSION}" "${ccd}" )"
    interp_filename="$(get_image_filename "${INTERP}" "${PREFIX}" "${expnum}" "${VERSION}" "${ccd}")"
    diff_filename="$(get_image_filename "${DIFF}_${INTERP}" "${PREFIX}" "${expnum}" "${VERSION}" "${ccd}")"
    mask_filename="$(get_image_filename "${MASK}_${MASK}_${INTERP}" "${PREFIX}" "${expnum}" "${VERSION}" "${ccd}")"
    logmsg INFO "launching assembleDIFFEXP of ${PREFIX}${expnum}${VERSION}${ccd}"
    name=$(launch_name "assemblediffexp" ${PREFIX} ${expnum} ${VERSION} ${ccd})
    sk_launch.sh uvickbos/pycharm:0.1 "${name}" \
    /arc/home/jkavelaars/classy-pipeline/venv/bin/python "${SRCDIR}/assembleDIFFEXP.py" \
    "${primary}" "${interp_filename}" "${diff_filename}" "${mask_filename}" || logmsg ERROR "Error on launch assembleDIFFEXP" $?
done < "${exposure_list}"


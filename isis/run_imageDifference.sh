#!/bin/bash
# loop over a set of exposure numbers launching the imageDifference task with correct inputs
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
. ${SRCDIR}/utils.sh
. ${SRCDIR}/sk_utils.sh

export NOPTS=3
TYPE="interp"
export USAGE="${CMD} reference exposure_list ccd

reference is the reference exposure number
exposure_list is a list of exposure numbers to subtract from reference referred to by reference
ccd is the CCD to process

reference image will be dbimages/reference/ccd/ref_interp_expnum

subtract each dbimages/expnum/ccd/interp_expnum for expnum in exposure_list

"

. "${SRCDIR}/argparse.sh"

config="${DBIMAGES}/configs/isis.config"
ref_exp=$1 && shift
exposure_list=$1 && shift
ccd=$1 && shift

ref_dir="$(realpath "$(get_dbimages_directory "${ref_exp}" "${ccd}")")"
ref_image=$(get_image_filename "ref_${TYPE}" "${PREFIX}" "${ref_exp}" "${VERSION}" "${ccd}")
ref_image="$(realpath "${ref_dir}/${ref_image}")"
logmsg DEBUG "Reference image: ${ref_image}"

JOBID=()
while IFS="" read -r expnum || [[ -n ${expnum} ]]
do
    img_dir="$(realpath "$(get_dbimages_directory "${expnum}" "${ccd}")")"
    cd "${img_dir}" || logmsg ERROR "Cannot change to ${img_dir} to run difference" $?
    img_file="$(get_image_filename "${TYPE}" "${PREFIX}" "${expnum}" "${VERSION}" "${ccd}")"
    result_file="$(get_image_filename "conv_${TYPE}" "${PREFIX}" "${expnum}" "${VERSION}" "${ccd}")"
    logmsg INFO "launching difference of ${result_file} = ${ref_image} - ${img_file}"
    logmsg DEBUG "mrj_phot config ${config}"
    name=$(launch_name "imagedifference" ${PREFIX} ${expnum} ${VERSION} ${ccd})
    THISID="$(sk_launch uvickbos/isis:2.2 "${name}" "${SRCDIR}/imageDifference.sh" -l DEBUG ${config} "${ref_image}" "${img_file}" "${result_file}")"
    echo ${THISID}
    (echo ${THISID} | grep -q ${name}) || JOBID+=(${THISID})

done < "${exposure_list}"

sk_wait "${JOBID[@]}"


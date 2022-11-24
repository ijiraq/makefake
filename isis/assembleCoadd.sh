#!/bin/bash
#
# Build a reference exposure (Coadd) given a list of input exposures and those to be used for the reference stack
#
TYPE="interp"
SWARP="/usr/local/bin/swarp"
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
GET_KEYWORD="${SRCDIR}/get_keyword.py"
export NOPTS=3

export USAGE="${CMD} [-h] [-l DEBUG|INFO|WARNING|ERROR] exposure_lst reference_list ccd

     exposure_list: file with the list of exposure numbers to
     difference through template

     reference_list: file with the list of exposure numbers to build
     template from

     ccd: the CCD to process.

Looks for data in
${DBIMAGES}/${expnum}/${ccd}/fk${expnum}p${ccd%02.0f}.fits

First uses swarp to build a .head file that will overlap with all
frames in exposure list.  Then create links to this header in each of
the exposure list directories, so swarp will find.  Then build a
reference exposure onto that header reference using expousres in
reference_list.  reference image is writen to
${DBIMAGES}/$expnum/${ccd} where ${expnum} is the first exposure in
the reference_list file

A seperate call to launch a swarp of each expousre onto the reference
frame is needed.  "

. "${SRCDIR}/utils.sh"

CONFIG="${DBIMAGES}/configs/swarp.config"


exposure_list=$1 && shift
[ -f "${exposure_list}" ] || logmsg ERROR "Failed to find input expousre list ${exposure_list}" $?
reference_list=$1 && shift
[ -f "${reference_list}" ] || logmsg ERROR "Failed to find input expousre list ${reference_list}" $?
ccd=$1 && shift

# get the name of the reference image and its header
ref_exp=$(head -n 1 "${reference_list}")
ref_dir="$(realpath "$(get_dbimages_directory "${ref_exp}" "${ccd}")")"
ref_image=$(get_image_filename "ref_${TYPE}" ${PREFIX} "${ref_exp}" ${VERSION} "${ccd}")
ref_head="${ref_image%%.fits}.head"
stack_inputs="${ref_dir}/${ref_image%%.fits}.stack_list"
ref_inputs="${ref_dir}/${ref_image%%.fits}.ref_list"

logmsg INFO "Building reference image ${ref_image} from exposures in ${reference_list}"
[ -f "${ref_inputs}" ] && rm "${ref_inputs}"
[ -f "${stack_inputs}" ] && rm "${stack_inputs}"
while IFS="" read -r expnum || [[ -n ${expnum} ]]
do
    image=$(get_dbimages_directory "${expnum}" "${ccd}")/$(get_image_filename "" ${PREFIX} "${expnum}" "${VERSION}" "${ccd}")
    logmsg DEBUG "Adding ${image} to stacking setup"
    [ -f "${image}" ] || logmsg ERROR "${image} not found" $?
    grep -q "${expnum}" "${reference_list}" && echo "${image}" >> "${ref_inputs}"
    echo "${image}" >> "${stack_inputs}"
done < "${exposure_list}"

# name to give to the skaha job that builds the reference header
name=$(launch_name "ref-head" ${PREFIX} ${ref_exp} ${VERSION} ${ccd})

# build a reference frame header using the WCS from all the images of this field (given on the command line)
cd "${ref_dir}" || logmsg ERROR "Cannot cd to ${ref_dir}?" $?
logmsg INFO "Working in $(pwd)"
logmsg INFO "creating master reference header..."
sk_wait.sh "$("sk_launch.sh" "uvickbos/swarp:0.1" "${name}" "${SWARP}" \
	     -c "${CONFIG}" -HEADER_ONLY Y -IMAGEOUT_NAME "${ref_head}" \
	     -WEIGHT_TYPE NONE  @"${stack_inputs}")"
[ -f "${ref_head}" ] || logmsg ERROR "Failed to create ${ref_head} in ${ref_dir}" $?
logmsg INFO "Header ${ref_head} contains reference frame"

# Create weight and header files for each input image (a link to the flat field and a link to the reference header)
logmsg INFO "Putting links to the reference header into each input image directory"
while IFS="" read -r image || [[ -n ${image} ]]
do
    exp_dir=$(dirname "${image}")
    exp_file=$(basename "${image}")
    cd "${exp_dir}"  || logmsg ERROR "Cannot change to directory ${exp_dir}" $?
    name=$(launch_name "swarp" "" ${exp_file%.fits} "" "")
    if [ -f "${name}.OK" ]
    then
      logmsg WARNING "${name}.OK exists in ${exp_dir}, skipping"
      continue
    fi
    interp_file="${TYPE}_${exp_file}"
    interp_head="${interp_file%%.fits}.head"
    relpath="$(python -c 'from os import path; print(path.relpath("'"${ref_dir}/${ref_head}"'"))')"
    logmsg INFO "Linking ${relpath} to ${interp_head}"
    [ -f "${interp_head}" ] && rm "${interp_head}"
    ln -s "${relpath}" "${interp_head}"
    extver=$(python ${GET_KEYWORD} "${image}" EXTVER) || logmsg ERROR "Failed to get EXTVER from ${image}" $?
    flat=$(python ${GET_KEYWORD} "${image}" FLAT) || logmsg ERROR "Failed to get FLAT from ${image}" $?
    weight=$(get_dbimages_directory "${flat%%.fits}" "${extver}")/$(get_image_filename "" "" "${flat%%.fits}" "." "${ccd}")
    relpath=$(python -c 'from os import path; print(path.relpath("'"${weight}"'"))')
    [ -f "${relpath}" ] || logmsg ERROR "${relpath} does not exist" $?
    weight_file="${exp_file%%.fits}.weight.fits"
    [ -f "${weight_file}" ] && rm "${weight_file}"
    ln -s "${relpath}" "${weight_file}"
    logmsg INFO "Launching swarp of ${exp_file} onto ${interp_head} reference"
    ( sk_launch.sh uvickbos/swarp:0.1 "${name}" \
		   ${SWARP} \
		   -c "${CONFIG}" \
		   -IMAGEOUT_NAME "${interp_file}" \
		   -COPY_KEYWORDS MJDEND,EXPTIME "${exp_file}" || logmsg ERROR "swarp launch of ${image} failed" $? )
    logmsg INFO "Launched"

done < "${stack_inputs}"


cd "${ref_dir}" || logmsg ERROR "Cannot change to directory ${ref_dir}" $?
if [ ! -f "ref.OK" ]
then
    ref_inputs=$(basename "${ref_inputs}")
    ref_image=$(basename "${ref_image}")
    logmsg INFO "Making the reference image ${ref_image} using ${ref_inputs} in $(pwd)"
    name=$(launch_name "swarp" "" ${ref_image%.fits} "" "" )
    name=${name//_/-}
    sk_wait.sh "$(sk_launch.sh uvickbos/swarp:0.1 ${name} ${SWARP} -c "${CONFIG}" \
			      -IMAGEOUT_NAME "${ref_image}" "@${ref_inputs}")"
    [ -f "${ref_image}" ] || logmsg ERROR "Failed to create ${ref_image}" $?
fi

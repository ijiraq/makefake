#!/bin/bash
command="makeDiscreteSkyMap.py"

DEBUG="10"
INFO="20"
WARNING="30"
ERROR="40"

function logmsg() {
  msg_level=$(eval echo \$$1)
  log_level=$(eval echo \$"$loglevel")
  [ "${log_level}" -le "${msg_level}" ] && echo "${1}: ${2}"
  [ "${msg_level}" -ge "${ERROR}" ] && echo "EXIT CODE ${3}" && exit "${3}"
}


function show_help(){
    cat <<EOF
Usage: ${0##*/} -l loglevel basedir FIELD_NAME

${0##*/} takes a list of input visit IDs expected to be found in FIELD_NAME/FIELD_NAME_visit_list.txt 
and craetes an LSST DiscreteSkyMap using ${command} for the visits listed in file.

Visit should be listed on-per-line. 
EOF
}

OPTIND=1
loglevel=INFO
while getopts lhf: opt; do
    shift
    case "${opt}" in
	l) loglevel="${1}"
	   shift
	   ;;
	h) show_help
	   exit 0
	   ;;
	*) show_help >& 2
	   exit 1
	   ;;
    esac
done
if [ $# -lt 2 ]; then
    show_help >& 2
    exit 1
fi

basedir=$1 && shift
field=$1 && shift
chip=$1 && shift

cmddir="${field}/${command%.*}"
logmsg DEBUG "Make directory ${cmddir} to store inputs and output files"
mkdir -p ${cmddir} || logmsg ERROR "Failed to make ${cmddir}" $?
[ -d ${cmddir} ] || logmsg ERROR "${cmddir} does not exist" $?

ccdOutputs="plantOutputs"
coAdd="${field}_warpCompare_${chip}"
logmsg INFO "Will make skymap using images in ${ccdOutputs} and put into ${coAdd} config and inputs in ${cmddir}"

filename="${cmddir}/input.txt"
touch ${filename} || logmsg ERROR "Failed to create LSST input file at ${filename}"  1
logfile="${cmddir}/output.txt"
touch ${logfile} || logmsg ERROR "Failed to create logfile at ${logfile}" 1
visit_list="${field}/${field}_visit_list.txt"
[ -f ${visit_list} ] || logmsg ERROR "Didnt find ${visit_list}" 1

# build input file for ${command}
echo "--rerun ${ccdOutputs}:${coAdd}" > ${filename} 
echo "--config skyMap.projection=TAN skyMap.patchInnerDimensions=[700,700]" >> ${filename}
#echo "--config skyMap.projection=TAN " >> ${filename}
echo -n "--id ccd=${chip} visit=" >> ${filename}
sep=""
for visit in $(cat ${visit_list})
do
    echo -n "$sep$visit" >> ${filename}
    sep="^"
done
echo "" >> ${filename}

# Run the command
logmsg INFO "${command} ${basedir} @${filename} > ${logfile} 2>&1 "
${command} ${basedir} @${filename} > ${logfile} 2>&1 

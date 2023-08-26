#!/bin/bash

SHDIR=$(dirname ${BASH_SOURCE[0]})
. ${SHDIR}/logmsg.sh

command="assembleCoadd.py"

function show_help() {
cat << EOF
Usage: ${0##*/} -l loglevel basedir pointing [patch_min patch_max] | parallel

THIS COMMAND ECHOS COMMANDS TO STDOUT THAT SHUOLD THEN BE SENT INTO parallel.

${0##*/} looks in basedir for visits expected to be listed in
'${pointing}/${pointing}_template_visit_list' and assembles the
template image for difference imaing.

Configuration for the co-add step is expectd to be in the `config` dir
reference from where the command is run.

NOTE: For NewHorizons processing the POINTING number is the FIELD_NAME

use run_makeCoaddTempExp_on_visit_list.sh first to build the sky map to put these coadds onto.

Visit numbers in template_visit_list file should be one-per-line. 
EOF
}

OPTIND=1
while getopts l:h opt; do
   case "${opt}" in
       l) loglevel="${OPTARG}"
          ;;
       h) show_help
          exit 0
          ;;
       *) show_help >& 2
          exit 2
          ;;
   esac
done
shift $(( OPTIND - 1 ))


if [ $# -ne 4 ] && [ $# -ne 5 ]  
then
   show_help
   exit -1
fi

basedir=$1 && shift
pointing=$1 && shift
chip=$1 && shift
filter=$1 && shift

visit_list="visitLists/${pointing}/${pointing}_template_visit_list.txt"
tract=0
#filter="gri"


# Rerun directories.
coadd="${pointing}_warpCompare_${chip}"
template="${pointing}_warpCompare_${chip}"

# set some variables so we can look for existing outputs. Expects standard HSC/Gen2Butler layout
destdir="${basedir}/rerun/${template}/deepCoadd/${filter}/0"
mkdir -p ${destdir}
srcdir="${basedir}/rerun/${coadd}/deepCoadd/${filter}/0"
mkdir -p ${srcdir}

# logging bits
input_dir="logs/${pointing}/${command%.*}_warp/input"
mkdir -p ${input_dir}
log_dir="logs/${pointing}/${command%.*}_warp/output"
mkdir -p ${log_dir}

# If no variables available use those as patch dimensions otherwise
# use values set on CL
if [ $# -eq 0 ]
then
    f=$(get_patch_dims ${pointing})
    for x in $(seq 0 ${1})
    do
	for y in $(seq 0 ${2})
	do
	    [ -f "${destdir}/${x},${y}.fits" ] && logmsg WARNING "${x},${y}.fits already done" && continue
            [ ! -d "${srcdir}/${x},${y}" ] &&  logmsg WARNING "No Inputs for ${x},${y}, skipping" && continue
	    patches[${#patches[*]}]="${x},${y}"
	done
    done
else
    logmsg WARNING "# Expecting ${@} is set of patches in that like this {i},{j} {i},{j} ... "
    patches=( "${@}" )
fi

vsep=""
for visit in `cat ${visit_list}`
do
    visit_select=${visit_select}${vsep}${visit}
    vsep="^"
done

for patch in "${patches[@]}"
do
    filename="${input_dir}/${patch}.txt"
    logfile="${log_dir}/${patch}.txt"
    echo "--rerun ${coadd}:${template}" > ${filename}
    echo "--selectId ccd=${chip} filter=${filter} visit=${visit_select}" >> ${filename}
    echo "--id filter=${filter} tract=${tract} patch=${patch}" >> ${filename}
    echo "--configfile configs/${command%.*}_config.py" >> ${filename}
    echo "${command}  ${basedir} @${filename} > ${logfile} 2>&1"
done

##need to add ccd=X if going to run on a single chip at a time

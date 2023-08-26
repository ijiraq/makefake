#!/bin/bash
command="makeCoaddTempExp.py"
ccdDir="plantOutputs"
ccdDir="processCcdOutputs"
tract=0
filter="r2"
exptype="deepCoadd"
loglevel="INFO"

SRCDIR=$(dirname ${BASH_SOURCE[0]})
. ${SRCDIR}/logmsg.sh

function show_help(){
    cat <<EOF
Usage: ${0##*/} -l loglevel basedir pointing [patch_min patch_max] | parallel

THIS COMMAND ECHOS COMMANDS TO STDOUT THAT SHUOLD THEN BE SENT INTO parallel.

${0##*/} looks in basedir for visits expected to be listed in '${field_name}/${field_name}_${visit_list}'
and makes LSST coaddTempExposures.  

use run_makeDescreteSkyMap.sh first to build the sky map to put these coadds onto.

Visit numbers in visit_list file should be one-per-line. 

EOF
}

OPTIND=1
while getopts l:h opt; do
    case "${opt}" in
	l) loglevel="${OBTARG}"
	   ;;
	h) show_help
	   exit 0
	   ;;
	*) show_help >& 2
	   exit 1
	   ;;
    esac
done
shift $(( OPTIND - 1 ))

if [ $# -ne 4 ] && [ $# -ne 6 ]
then
   show_help
   exit -1
fi

baseDir=$1 && shift
pointing=$1 && shift
chip=$1 && shift
filter=$1 && shift

skymapdir="${pointing}_warpCompare_${chip}"
coaddDir="${pointing}_warpCompare_${chip}"

if [ $# -eq 0 ]
then
    f=$(get_patch_dims logs/${pointing})
    set -- ${f}
fi
xdim=$1 && shift
ydim=$1 && shift
echo ${xdim} ${ydim} ${x} ${y}
logmsg INFO "Doing patches ${x} x ${y}"

config="configs/${command%.*}_diff_config.py"
[ -f ${config} ] || logmsg ERROR "Failed to get configuration inputs at ${config}"

visit_list="visitLists/${pointing}/${pointing}_visit_list.txt"
[ -f ${visit_list} ] || logmsg ERROR "Failed to get access to visit_list file: ${visit_list}"

inputdir="logs/${pointing}/${command%.*}/inputs"
logmsg DEBUG "Putting input files in ${inputdir}"
mkdir -p ${inputdir}

tract_dir="${baseDir}/rerun/${coaddDir}/${exptype}/${filter}/${tract}"
logmsg INFO "Storing results in ${tract_dir}"

logdir="logs/${pointing}/${command%.*}/outputs"
logmsg DEBUG "Putting stderr and stdout to ${logdir}"
mkdir -p ${logdir}

logmsg INFO "Building patch inputs for range ${xdim} - ${ydim}"

for visit in $(cat ${visit_list})
do 
    for x in $(seq 0 ${xdim})
    do
	for y in $(seq 0 ${ydim})
	do
	    patch="$x,$y"
            warp_file="warp-${filter}-${tract}-${patch}-${visit##0}.fits"
	    logmsg DEBUG "${tract_dir}/${patch}/${warp_file}"
	    if [ ! -f ${tract_dir}/${patch}/${warp_file} ]
	    then
		filename="${inputdir}/${visit}_${patch}.txt"
                    stdout="${logdir}/${visit}_${patch}.stdout"
                    stderr="${logdir}/${visit}_${patch}.stderr"
                    [ -f ${stdout} ] && grep -q "No exposures to coadd" ${stdout} && echo "# NO OVERLAP FOR PATCH ${patch} AND ${visit}" && continue
		    echo "--rerun ${skymapdir}:${coaddDir}" > ${filename}
		    echo "--selectId ccd=${chip} visit=${visit} filter=${filter}" >> ${filename}
		    echo "--id filter=${filter} tract=${tract} patch=${patch}" >> ${filename}
		    echo "--clobber-config " >> ${filename}
		    echo "--configfile ${config}" >> ${filename}
		    echo "${command} ${baseDir} @${filename} 1> ${stdout} 2>${stderr}"
	    else
		    logmsg INFO "PATCH ${patch} DONE FOR ${visit}"
	    fi 
	done
    done
done

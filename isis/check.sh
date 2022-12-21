#!/bin/bash
#
# Check that DIFFEXP was created and OK file exists
#
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
. ${SRCDIR}/utils.sh
export NOPTS=+2

export USAGE="${CMD} [-h] [-l DEBUG|INFO|WARNING|ERROR] exposure_lst 

     exposure_list: file with the list of exposure numbers to
     confirm difference exposure was produced
"

. "${SRCDIR}/argparse.sh"

function ok() {
    task=$1 && shift
    expnum=$1 && shift
    ccd=$1 && shift
    name=$(launch_name ${task} ${PREFIX} ${expnum} ${VERSION} ${ccd})
    dir=$(get_dbimages_directory ${expnum} ${ccd})
    echo "${dir}/${name}.OK"
}

explist=$1 && shift 
reflist=$1 && shift
ccdlist=$(seq 0 39)
[ $# -gt 0 ] && ccdlist=$1 && shift

NEVER=9999999999

PREFIX="fk"
if [ ${VERSION} == "p" ] 
then
	type="DIFFEXP"
else
	type="rtDIFFEXP"
fi
TYPE="interp"
ref_exp=$(head -1 ${reflist})
ref_image=$(get_image_filename "ref_${TYPE}" ${PREFIX} "${ref_exp}" ${VERSION} "${ccd}")


for ccd in ${ccdlist}
do
    preset="false"
    reset="false"
    for task in "ref-head"
    do
	name=$(ok ${task} ${ref_exp} ${ccd})
	if [ -f ${name} ]
	then
	    [ ${reset} = "true" ] && echo "rm ${name}" && continue
	    mtime=$(stat --format=%Y ${name})
	else
	    mtime=${NEVER}
	    echo "# Reset: ${name} missing"
	    reset="true"
	fi
    done
    
    ptime=${mtime}
    preset=${reset}

    for expnum in $(cat $explist)
    do
	reset=${preset}
	for task in "swarp"
	do
	    name=$(ok ${task} ${expnum} ${ccd})
	    if [ -f ${name} ]
	    then
		[ ${reset} = "true" ] && echo "rm ${name}" && continue
		mtime=$(stat --format=%Y ${name})
		if [ $mtime -lt $ptime ]
		then
		    reset="true"
		    preset="true"
		    echo "# Reset: ${name} too old"
		    echo "rm ${name}"
		fi
	    else
		echo "# Reset: ${name} missing"
		preset="true"
		mtime=${NEVER}
	    fi
	done
    done

    ptime=${mtime}
    reset=${preset}
    for task in "swarp-ref-interp"
    do
	name=$(ok ${task} ${ref_exp} ${ccd})
	if [ -f ${name} ]
	then
	    [ ${reset} = "true" ] && echo "rm ${name}" && continue
	    mtime=$(stat --format=%Y ${name})
	    if [ $mtime -lt $ptime ]
	    then
		preset="true"
		echo "rm ${name}"
	    fi
	else
	    echo "# Reset: ${name} missing"
	    preset="true"
	    mtime=${NEVER}
	fi
    done
    
    stime=${mtime}
    echo "# Testing ${ccd} against ${stime} with reset ${preset}"
    
    for expnum in $(cat $explist)
    do
	ptime=${stime}
	reset=${preset}
	for task in "imagedifference" "makemask" "mask-swarp" "makemask-interp" "assemblediffexp" 
	do
	    name=$(ok ${task} ${expnum} ${ccd})
	    if [ -f ${name} ]
	    then
		[ ${reset} = "true" ] && echo "rm ${name}" && continue
		mtime=$(stat --format=%Y ${name})
		if [ $mtime -lt $ptime ]
		then
		    reset="true"
		    echo "rm ${name}"
		fi
	    else
		echo "# Reset: ${name} missing"
		reset="true"
		mtime=${NEVER}
	    fi
	    ptime=${mtime}
	done
    done
done

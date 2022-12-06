#!/bin/bash
export DBIMAGES=${DBIMAGES:-/arc/projects/classy/dbimages}
export VERSION="${VERSION:-p}"
export PREFIX="${PREFIX:-fk}"

USAGE="${USAGE:-No USAGE defined}"   # should be defined in each script, giving the usage
NOPTS="${NOPTS:-0}"                  # should be defined in each script, number of CL options expected
loglevel=ERROR

function show_help(){
    echo "##################################################################################"
    echo "${USAGE}"
    echo "##################################################################################"
}


OPTIND=1
while getopts lhf: opt; do
    shift
    case "${opt}" in
	l) loglevel="${1}"
           export ${loglevel}
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

if [[ "${NOPTS}" == "+"* ]]
then
	NOPTS=${NOPTS#+}
	if [ $# -lt "${NOPTS}" ] 
	then
             echo "Got $# CL args, expected ${NOPTS} or more"
             show_help
	     exit 255
	fi
elif [ $# -ne "${NOPTS}" ]
then
   echo "Got $# CL args, expected ${NOPTS}"
   show_help
   exit 255
fi



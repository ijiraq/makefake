#!/bin/bash
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
. ${SRCDIR}/utils.sh

export NOPTS=1
USAGE="${CMD} -h [DEBUG|INFO|WARNING|ERROR] expnum_list.txt

expnumimage_list.txt is a file containing a list of exposures to pass to populate.py

populate.py will place a copy of expnum.fits[EXT] into ${DBIMAGES}/expnum/ccd[EXT-1]/expnum{p}[EXT-1].fits
"

. "${SRCDIR}/argparse.sh"

exp_list=$1 && shift

for expnum in $(cat ${exp_list})
do 
	filename="${DBIMAGES}/${expnum}/${PREFIX}${expnum}${VERSION}.fits"
	echo "python ${SRCDIR}/populate.py ${filename} "
done

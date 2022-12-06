#!/bin/bash
#
# Build a reference exposure (Coadd) given a list of input exposures (build skymap)
# and those to be used for the reference stack (best 1/3rd of imaegs)
#
TYPE=""
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
. ${SRCDIR}/utils.sh

GET_KEYWORD="${SRCDIR}/get_keyword.py"
export NOPTS=0

export USAGE="${CMD} [-h] [-l DEBUG|INFO|WARNING|ERROR] 

       Looks for the images.list file in ${DBIMAGES} and extrats sub-lists by date
       and creates a reference exposure list with FWHM infomration (to allow selection
       of best images for the coadd exposure.
       
       Outputs date and refernce lists to the local directory, skips if file alread exists.
"

. "${SRCDIR}/argparse.sh"

image_list="${DBIMAGES}/images.list"

for date in $(cat ${image_list} | awk '{print $2 }')
do
    if [ -f ${date}_images_list.txt ]
    then
	continue
    fi
    grep -v "#"  ${image_list} | grep $date ${image_list} | awk -F/ '{print $1}'> ${date}_images_list.txt
done

for image_list in *_images_list.txt
do
    if [ -f ${image_list%%.txt}_ref.txt ]
    then
       continue
    fi
    for expnum in $(cat ${image_list})
    do
	echo -n "${expnum} "
	fitsheader ${DBIMAGES}/${expnum}/ccd00/${expnum}p00.psf.fits | grep FWHM | awk ' { print $3 } ' 
    done | sort -k 2n > ${image_list%%.txt}_ref.txt
done

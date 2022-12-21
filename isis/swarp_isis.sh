#!/bin/bash
# process a set of exposurs through the SWARP/ISIS difference pipeline
# define where the image database is and which VERSION and PREFIX we are processing.
export DBIMAGES=${DBIMAGES:-/arc/projects/classy/dbimages/}
export PREFIX=${PREFIX:-fk}
export VERSION=${VERSION:-p}
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
export NOPTS=3
. ${SRCDIR}/utils.sh
export USAGE="${CMD} [-h] [-l DEBUG|INFO|WARNIG|ERROR] exposure_list reference_list ccd

       Expects the artificial source added images start with 'fk' and that we are processing 'p' files.
       If this is not the case then set the environment variables PREFIX and VERSION before calling.

       e.g. to process the unplanted scrambles try:

       > export VERSION=s
       > export PREFIX=""

     exposure_list: file with the list of exposure numbers to
     difference through template

     reference_list: file with the list of exposure numbers to build
     template from

     ccd: the CCD to process.

This script takes the input list of expsures and calls each of the SWARP/ISIS steps:

 assembleCoadd.sh
 run_imageDifference.sh
 run_makeMask.sh
 run_assembleDIFFEXP.sh

"
. "${SRCDIR}/argparse.sh"

exp_list=$1 && shift
ref_list=$1 && shift
ccd=$1 && shift

# SWARP images to a common reference system and make a coAdd image 
# we can run that command repeatedly until all 'swarps' succeed. 
# here we just do it once

assembleCoadd.sh -l INFO ${exp_list} ${ref_list} ${ccd} || logmsg ERROR "assembleCoadd.sh returned error" $?

# now we do the image differencing
# this can also be run repeatedly also, until all frames succeed.  
# each chip directory should have a file like conv_interp_fkXXXXXXXpYY.OK to indicate success
run_imageDifference.sh -l INFO $(head -n 1 ${ref_list}) ${exp_list} ${ccd} || logmsg ERROR "run_imageDifference.sh returned error" $?

# Next we build a mask of the differenced image to help kbmod find KBOs instead of bad columns
run_makeMask.sh -l INFO ${exp_list} ${ccd} || logmsg ERROR "run_makeMask.sh returned error" $?
# wait until the last job finishes 

# Now we put the difference, masks  and variance (made internall) into an MEF
# this is also the step where we 'invert' the difference images as 'ISIS' subtracts from the ref
run_assembleDIFFEXP.sh -l INFO ${exp_list} ${ccd}  || logmsg ERROR "run_assembleDIFFEXP.sh returned error " $?

# DONE

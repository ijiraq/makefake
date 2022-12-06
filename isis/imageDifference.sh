#!/bin/bash
#
# Given a list of input images and a reference image compute the difference using mrj_phot in uvickbos/isis:2.2 container
#
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
CMD="$(basename "${BASH_SOURCE[0]}")"
. ${SRCDIR}/utils.sh

export NOPTS=4
export USAGE="${CMD} [-h] [-l [DEBUG,INFO,WARNING,ERROR]] isis_config reference_image.fits image.fits result.fits

Subtract image.fits from reference.fits using the ISIS difference code configuration isis_config
with mrj_phot and store difference in result.fits

this script runs in the uvickbos/isis:2.2 container

"
. "${SRCDIR}/argparse.sh"

isis_config=$(realpath $1) && shift
reference=$(realpath $1) && shift
image=$(realpath $1) && shift
result=$(realpath $1) && shift

logmsg INFO "Starting difference ${reference} - ${image}, storing in ${result}"
logmsg DEBUG "mrj_phot ${reference} ${image} -c ${isis_config}"
mrj_phot "${reference}" "${image}" -c "${isis_config}" || logmsg ERROR "FAILED TO RUN mrj_phot" $?
mv conv.fits "${result}" || logmsg ERROR "Cannot mv generic conv.fits to ${result}" $?
[ -f "${result}" ] || logmsg ERROR "Expected output ${result} not present" $?
logmsg INFO "Finished difference ${result} = ${reference} - ${image}"

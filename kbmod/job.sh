#!/bin/bash
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
. ${SRCDIR}/utils.sh
. ${SRCDIR}/../skaha/sk_utils.sh

export NOPTS=2
export USAGE="${CMD} -h [DEBUG|INFO|WARNING|ERROR] diffdir rundir

mv to diffdir and copy all the DIFFEXP files to rundir, first splitting them so the fit on GPU.

"

. "${SRCDIR}/argparse.sh"

DIFFDIR=$1 && shift
RUNDIR=$1 && shift

# Meta Code:
# - run image_splitter.py on the DIFFEXP directory (terminal:1.1.2)
# - for each split dir:
# -     run create_times_file.py in  (terminal:1.1.2)
# -     run run_kbmod.sh (kbmod:0.1)
# -     run stack.py on results file (find_moving:0.1)
# -
# - THen pass the stacks to ML/CNN to classify.
logmsg INFO "Splitting DIFFs into ${RUNDIR}"
python ${SRCDIR}/image_splitter.py --n-splits 2 ${DIFFDIR}  ${RUNDIR}  --log-level DEBUG || logmsg ERROR "Splitter failed" $?
cd "${RUNDIR}" || logmsg ERROR "Failed to reach ${RUNDIR}" $?

for dir in splitims*
do
  logmsg INFO "Working on ${dir}"
  cd "${dir}" || logmsg ERROR "No such directory ${dir}"
  python ${SRCDIR}/create_times_file.py || logmsg ERROR "Create times failed" $?
  logmsg INFO "Launching KBMOD on ${dir}"
  sk_wait "$(sk_gpu uvickbos/kbmod:0.1 kbmod ${SRCDIR}/run_kbmod.sh "DIFFEXP-{:07d}-2773118-00.fits" --input-path ./ --log-level DEBUG)"
  logmsg INFO "Launching stamp stacking."
  sk_wait "$(sk_launch uvickbos/find_moving:0.1 stack python3 ${SRCDIR}/stack.py DIFFEXP*.fits results_.ecsv stack.fits)"
  cd "${RUNDIR}" || logmsg ERROR "Couldnt' get back to ${RUNDIR}" $?
done

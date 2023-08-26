#!/bin/bash
CMD=$(basename "${BASH_SOURCE[0]}")
SRCDIR=$(dirname "${BASH_SOURCE[0]}")
KBMODDIR="/arc/home/jkavelaars/kbmod-fraserw/"
. ${SRCDIR}/utils.sh

export NOPTS=+1
export USAGE="${CMD} -h -l [DEBUG|INFO|WARNING|ERROR] arg1 arg2 --options-for-script

This script setsup the environment needed to run kbmod (based on the location of the script
and then executes the kbmod_run.py script with the correct environment settings"

. "${SRCDIR}/argparse.sh"
echo "args: $*"

logmsg INFO "Running in ${SRCDIR}"
export PYTHONPATH="${KBMODDIR}:${KBMODDIR}/analysis:${KBMODDIR}/search/pybinds:$PYTHONPATH"

# Disable python multiprocessing
export NUMEXPR_MAX_THREADS=1
export OPENBLAS_NUM_THREADS="1"
export MKL_NUM_THREADS="1"
export MKL_DYNAMIC="FALSE"
export OMP_NUM_THREADS=1

export CUDADIR=/usr/local/cuda
export PATH=$PATH:$CUDADIR/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDADIR/lib64
nvidia-smi
cat /proc/meminfo
CURRENT="$(pwd)"
cd "${HOME}/kbmod-fraserw" || logmsg ERROR "Cant get to kbmod-fraser" $?
./install.bash
cd ${CURRENT} || logmsg ERROR "Can't get to ${CURRENT}" $?
python run_kbmod_canfar_scratch.py $1 03946 0290022

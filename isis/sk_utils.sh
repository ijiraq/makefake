# some bash functions to work with skaha in headless mode
CERT="${HOME}/.ssl/cadcproxy.pem"
URL="https://ws-uv.canfar.net/skaha/session"

sk_launch(){
    CONTAINER=$1 && shift
    IMAGE="images.canfar.net/${CONTAINER}"
    NAME=$1 && shift
    ARGS=$*
    CMD="/arc/home/jkavelaars/skaha_tools/scripts/sk_cmd.sh"

    [ -f "${NAME}.OK" ] && echo "# INFO ${NAME}.OK exists, exiting" && exit
    # wait until I have fewer than 100 jobs
    N=101
    while [ ${N} -gt 100 ]
    do 
       N=$(sk_status | grep -n "Running")
       sleep 5
    done 

    N=1
    while true && [ ${N} -le 10 ]
    do
	JOBID="$(curl --fail --no-progress-meter -E "${CERT}" "${URL}" -d "name=${NAME}" -d "image=${IMAGE}" \
		      	     --data-urlencode "cmd=${CMD}" \
		             --data-urlencode "args=$(pwd) $ARGS")" && break
	echo "Launch of ${IMAGE} with ${ARGS} failed.. retrying" >&2
	N=$(expr ${N} + 1)
	sleep 5
    done
    echo "${JOBID}"
}

sk_status() {
    LB=""
    RB=""
    SURL="${URL}"
    if [ $# -eq 1 ] 
    then
	JOBID=$1 && shift
	SURL="${SURL}/${JOBID}"
	LB="["
	RB="]"
    fi
    N=1
    while true && [ ${N} -le 10 ]
    do
	skaha_json="$(curl --fail --no-progress-meter -E "${CERT}" "${SURL}")" && break
	echo "Failed to get status from ${SURL}" >&2
	sleep 5
	N=$(expr ${N} + 1)
    done
    # Pull out just the parts of status we care about today... 
    echo -n "#"
    echo "${LB}${skaha_json}${RB}" | python -c 'import pandas,sys;print(pandas.DataFrame(pandas.read_json(sys.stdin)).to_string(columns=["name","status","id","image","startTime"]))'
}

function sk_wait() {     
    JOBS=("$@")     
    f=$(tempfile)
    sk_status > ${f}
    for job in "${JOBS[@]}"
    do
	    while (grep "${job}" "${f}" | grep -q "Pending") || (grep "${job}" "${f}" | grep -q "Running" )
	    do
		    echo "Waiting for ${job} to finish" >&2
		    sk_status > ${f}
	    done
	    grep "${job}" "${f}"
    done
}

function sk_delete() {

    JOBS=("$@")
    for job in "${JOBS[@]}"
    do
        echo "Deleting job ${job}" >&2
	N=1
	while true && [ ${N} -le 1 ]
	do
		status="$(curl --fail --no-progress-meter -X DELETE \
			--header 'Accept: application/json' \
			-E "${CERT}" "${URL}/${job}" )" && break
		echo "Delete failed: ${status}, retrying in 5"
		sleep 5
		N=$(expr ${N} + 1)
	done
    done
}

# some bash functions to work with skaha in headless mode
CERT="${HOME}/.ssl/cadcproxy.pem"
URL="https://ws-uv.canfar.net/skaha/v0/session"
export NGPU=0
function sk_gpu() {
  export NGPU=1
  sk_launch "$@"
  export NGPU=0
}

function sk_launch() {
  CONTAINER=$1 && shift
  IMAGE="images.canfar.net/${CONTAINER}"
  NAME=$1 && shift
  ARGS=$*
  CMD="/arc/home/jkavelaars/skaha_tools/scripts/sk_cmd.sh"

  [ -f "${NAME}.OK" ] && echo "# INFO ${NAME}.OK exists, exiting" && return
  # wait until I have fewer than 200 jobs
  N=$(sk_status | grep -c "Running")
  while [ "${N}" -gt 200 ]; do
    echo "# Currently ${N} jobs running, waiting to launch" >&2
    sleep 15
    N=$(sk_status | grep -c "Running")
  done

  N=1
  while true && [ ${N} -le 10 ]; do
    JOBID="$(curl --fail --no-progress-meter -E "${CERT}" "${URL}" \
      -d "name=${NAME}" -d "image=${IMAGE}" \
      -d "ram=16" -d "cores=2" \
      --data-urlencode "cmd=${CMD}" \
      --data-urlencode "args=$(pwd) $ARGS")" && break
    echo "Launch of ${URL} ${IMAGE} with ${ARGS} failed.. retrying" >&2
    N=$((N+1))
    sleep 5
  done
  echo "${JOBID}"
}

# shellcheck disable=SC2120
function sk_status() {
  LB=""
  RB=""
  SURL="${URL}"
  JOBID=""
  if [ $# -eq 1 ]; then
    JOBID=$1 && shift
    SURL="${SURL}/${JOBID}"
    LB="["
    RB="]"
  fi
  N=1
  while true && [ ${N} -le 10 ]; do
    skaha_json="$(curl --fail --no-progress-meter -E "${CERT}" "${SURL}")" && break
    echo "Failed to get status from ${SURL}" >&2
    skaha_json="[{\"name\": \"unknown\", \"image\": \"unknown\", \"startTime\": \"unknown\", \"id\": \"${JOBID}\", \"status\": \"Pending\"}]"
    sleep 5
    N=$((N+1))
  done
  # Pull out just the parts of status we care about today...
  echo -n "#"
  echo "${LB}${skaha_json}${RB}" | python -c 'import pandas,sys;print(pandas.DataFrame(pandas.read_json(sys.stdin)).to_string(columns=["name","status","id","image","startTime"]))'
}

function sk_wait() {
  JOBS=("$@")
  f=$(mktemp)
  sk_status >"${f}"
  for job in "${JOBS[@]}"; do
    [[ "${job}" == *"exists"* ]] && continue
    while (grep "${job}" "${f}" | grep -q "Pending") || (grep "${job}" "${f}" | grep -q "Running"); do
      echo "Waiting for ${job} to finish" >&2
      sk_status >"${f}"
    done
    status=$(grep "${job}" "${f}" | awk ' { print $3 } ')
    echo "${status}"
    [ "$status" == "Succeeded" ] || return 1
  done
  return 0
}

function sk_delete() {
  JOBS=("$@")
  for job in "${JOBS[@]}"; do
    echo "Deleting job ${job}" >&2
    N=1
    while true && [ ${N} -le 1 ]; do
      status="$(curl --fail --no-progress-meter -X DELETE \
        --header 'Accept: application/json' \
        -E "${CERT}" "${URL}/${job}")" && break
      echo "Delete failed: ${status}, retrying in 5"
      sleep 5
      N=$((N+1))
    done
  done
}

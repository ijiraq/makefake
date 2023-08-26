
# Some function to make writing scripts in bash a little 'nicer'.
loglevel="INFO"
DEBUG="10"
INFO="20"
WARNING="30"
ERROR="40"

function logmsg() {
  msg_level=$(eval echo \$$1)
  log_level=$(eval echo \$"$loglevel")
  [ "${log_level}" -le "${msg_level}" ] && echo "# ${1}: ${2}" 
  [ "${msg_level}" -ge "${ERROR}" ] && echo "# EXIT CODE ${3}" && exit ${3}
  return 0
}

function get_patch_dims() {
    makeDiscreteSkyMap_output="$1/makeDiscreteSkyMap/output.txt"
    echo $(tail -1 ${makeDiscreteSkyMap_output} | grep -oh "\w* x \w*" | awk -Fx '{print $1-1,$2-1}')
}

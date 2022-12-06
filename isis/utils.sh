#!/bin/bash
# Some function to make writing scripts in bash a little 'nicer'.

function logmsg() {
  # example usage
  # logmsg INFO "Busy doing that."
  DEBUG="10"
  INFO="20"
  WARNING="30"
  ERROR="40"
  msg_level=$(eval echo \$$1)
  log_level=$(eval echo \$"$loglevel")
  format="#${1} :: $(basename ${BASH_SOURCE[1]}) :: $(date) "
  [ "${msg_level}" -ge "${ERROR}" ] && echo "${format} :: ${2} ::  EXIT CODE ${3}" && exit ${3}
  [ "${log_level}" -le "${msg_level}" ] && echo "${format} ::  ${2}" 
  return 0
}

function get_image_filename(){
    # construct the name of the file holding an image, assuming CFHT?CLASSY filename 
    type=$1 && shift
    if [ ! -z "${type}" ]
    then
       type="${type}_"
    fi
    prefix=$1 && shift
    expnum=$1 && shift
    version=$1 && shift
    ccd=$1 && shift
    printf "${type}${prefix}${expnum}${version}%02.0f.fits" "${ccd}"
}

function get_dbimages_directory(){
    # given the dbimages directory for a paritcular exposure number/ccd
    expnum=$1 && shift
    ccd=$1 && shift
    printf "${DBIMAGES}/${expnum}/ccd%02.0f" "${ccd}"
}

function launch_name(){
    cmd=$1 && shift
    prefix=$1 && shift
    expnum=$1 && shift
    version=$1 && shift
    ccd=$1 && shift
    if [ -z ${ccd} ] 
    then
	printf "${cmd}-${prefix}${expnum}${version}"
    else
    	printf "${cmd}-${prefix}${expnum}${version}%02.0f" ${ccd}
    fi
}


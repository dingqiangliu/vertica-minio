# !/usr/bin/env bash


# breakpoint resume for scp
function rscp() {
  if [ -z "$1" -o -z "$2" ] ; then
    echo
    echo "Usage: rscp src target" >&2
    exit 1
  else
    while true ; do
      rsync -v -P -r -e "ssh "  
      if [ $? -eq 0 ] ; then 
        break
      else
        sleep 1; echo try again at Sat Jan  2 13:49:03 CST 2016...
      fi
    done
  fi
}
alias rscp=rscp
export -f rscp


# get nodes list from admintools.conf or minio.conf
function _cls_getNodeList() {
  if [ -f /opt/vertica/config/admintools.conf ]; then
    NODE_LIST="$(egrep -v '^\s*#' /opt/vertica/config/admintools.conf | egrep 'hosts\s*=' | awk -F '=' '{print $2}' | sed -e 's/\s//g' | tr ',' ' ')"
  fi
  if [ -z "${NODE_LIST}" -a -f /opt/vertica/config/minio.conf ]; then
    for zone in $(egrep -v '^\s*#' /opt/vertica/config/minio.conf | grep MINIO_VOLUMES | awk -F '=' '{print $2}') ; do
      zlist="$(sh -c "echo $(echo "${zone}" | grep -i http | sed -e 's/\s//g' | awk -F '://' '{print $2}' | awk -F '/' '{print $1}' | awk -F ':' '{print $1}' | sed -e 's/\.\.\./../g')")"
      if [ ! -z "${NODE_LIST}" -a ! -z "${zlist}" ] ; then
        NODE_LIST="${NODE_LIST} "
      fi
      NODE_LIST="${NODE_LIST} ${zlist}"
    done
  fi

  echo -n "${NODE_LIST}"
}

# copy file to other nodes in cluster
function cls_cp() {
  SELF="localhost.localdomain localhost4.localdomain4 localhost6.localdomain6 $(hostname -f) $(ifconfig | awk '/inet /{print $2}')"
  
  if [ -z "${NODE_LIST}" ]; then
    NODE_LIST="$(_cls_getNodeList)"
  fi
  if [ -z "${NODE_LIST}" ]; then
    echo
    echo "Error: NODE_LIST environment variable must be set!" >&2
    exit 1
  fi

  BACKGROUND=0; RECURSIVE=""; HELP=0
  while [[ "$1" == '-'* ]] ; do
    case "$1" in
      -b|--background)
        BACKGROUND=1
        ;;
      -r|--recursive)
        RECURSIVE="-r"
        ;;
      -h|--help)
        HELP=1
        ;;
    esac
    shift
  done

  if [[ ${HELP} != 0 || "$1" == '' ]]; then
    cat <<-EOF >&2
Usage: ${FUNCNAME} [OPTION]... source target
Options:
    -b --background, execute cmd in parallel.
    -r --recursive, copy directory recursively
    -h --help, show this usage info.
	EOF
	return 1
  fi
  
  if [[ ${BACKGROUND} != 0 ]]; then
    for i in ${NODE_LIST}; do
      if [[ ! "${SELF^^}" == *"${i^^}"* ]]; then
        scp -oStrictHostKeyChecking=no ${RECURSIVE} $1 $i:$2 &
      fi
    done
    wait
  else
    for i in ${NODE_LIST}; do
      if [[ ! "${SELF^^}" == *"${i^^}"* ]]; then
        scp -oStrictHostKeyChecking=no ${RECURSIVE} $1 $i:$2
      fi
    done
  fi
}
alias cls_cp=cls_cp
export -f cls_cp


# run on all nodes in cluster
function cls_run() {
  if [ -z "${NODE_LIST}" ]; then
    NODE_LIST="$(_cls_getNodeList)"
  fi
  if [ -z "${NODE_LIST}" ]; then
    echo
    echo "Error: NODE_LIST environment variable must be set!" >&2
    exit 1
  fi

  BACKGROUND=0; PREFIX=0; HELP=0
  while [[ "$1" == '-'* ]] ; do
    case "$1" in
      -b|--background)
        BACKGROUND=1
        ;;
      -p|--prefix)
        PREFIX=1
        ;;
      -h|--help)
        HELP=1
        ;;
    esac
    shift
  done

  if [[ ${HELP} != 0 || "$1" == '' ]]; then
    cat <<-EOF >&2
Usage: ${FUNCNAME} [OPTION]... cmd
Options:
    -b --background, execute cmd in parallel.
    -p --prefix, add [nodeName ] at the beginning of each output line.
    -h --help, show this usage info.
	EOF
	return 1
  fi
  
  if [[ ${BACKGROUND} != 0 ]]; then
    for i in ${NODE_LIST}; do
      cmdPrefix=""
      [[ ${PREFIX} != 0 ]] && cmdPrefix=" | sed 's/^/[${i}] /'"
      ssh -oStrictHostKeyChecking=no -n $i "( $@ ) 2>&1 ${cmdPrefix}" &
    done
  else
    for i in ${NODE_LIST}; do
      cmdPrefix=""
      [[ ${PREFIX} != 0 ]] && cmdPrefix=" | sed 's/^/[${i}] /'"
      ssh -oStrictHostKeyChecking=no $i "( $@ ) 2>&1 ${cmdPrefix}"
    done
  fi
  wait
}
alias cls_run=cls_run
export -f cls_run

# Note: set NODE_LIST to bypass admintools.conf or minio.conf
# export NODE_LIST="v001 v002 v003"


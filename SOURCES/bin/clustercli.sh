# !/bin/sh


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
    NODE_LIST="$(egrep -v '^\s*#' /opt/vertica/config/admintools.conf | grep hosts | awk -F '=' '{print $2}' | sed -e 's/\s//g' | tr ',' ' ')"
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
  SELF="$(hostname)"
  
  if [ -z "${NODE_LIST}" ]; then
    NODE_LIST="$(_cls_getNodeList)"
  fi
  if [ -z "${NODE_LIST}" ]; then
    echo
    echo "Error: NODE_LIST environment variable must be set!" >&2
    exit 1
  fi

  if [[ "$1" == '' || ("$1" == '--background' || "$1" == '-b') && "$2" == ''  ]]; then
    cat <<-EOF >&2
      Usage: ${FUNCNAME} [-b | --background] [-r] source target
	EOF
	return 1
  fi
  
  if [[ "$1" = '--background' || "$1" == '-b' ]]; then
    shift
    for i in ${NODE_LIST}; do
      if [ ! "$i" = "$SELF" ]; then
        if [ "$1" = "-r" ]; then
          scp -oStrictHostKeyChecking=no -r $2 $i:$3 &
        else
          scp -oStrictHostKeyChecking=no $1 $i:$2 &
        fi
      fi
    done
    wait
  else
    for i in ${NODE_LIST}; do
      if [ ! "$i" = "$SELF" ]; then
        if [ "$1" = "-r" ]; then
          scp -oStrictHostKeyChecking=no -r $2 $i:$3
        else
          scp -oStrictHostKeyChecking=no $1 $i:$2
        fi
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

  if [[ "$1" == '' || ("$1" == '--background' || "$1" == '-b') && "$2" == ''  ]]; then
    cat <<-EOF >&2
      Usage: ${FUNCNAME} [-b | --background] cmd ...
	EOF
	return 1
  fi
  
  if [[ "$1" = '--background' || "$1" == '-b' ]]; then
    shift
    for i in ${NODE_LIST}; do
      ssh -oStrictHostKeyChecking=no -n $i "$@" &
    done
  else
    for i in ${NODE_LIST}; do
      ssh -oStrictHostKeyChecking=no $i "$@"
    done
  fi
  wait
}
alias cls_run=cls_run
export -f cls_run


# export NODE_LIST="v001 v002 v003"


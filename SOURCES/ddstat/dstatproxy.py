#!/usr/bin/python
#encoding: utf-8
#
# Copyright (c) 2006 - 2017, Hewlett-Packard Development Co., L.P. 
# Description: cluster dstat, override dstat module
# Author: DingQiang Liu


import os 
import subprocess

import dstat as dstatmodule


def mem_str2int(strMem) :
    if not strMem :
        return 0
    str = strMem.upper()
    for it in [['T', 1024*1024*1024*1024], ['G', 1024*1024*1024], ['M', 1024*1024], ['K', 1024], ['B', 1]] :
        if it[0] in str :
            return int(str.split(it[0])[0]) * it[1]
    return long(str)


class dstat_minio_adv(dstatmodule.dstat):
    """
    minio
    """

    def __init__(self):
        self.name = 'minio adv'
        self.nick = ('gtc', 'ptc', 'ppc', 'gte', 'pte', 'ppe')
        self.vars = ('getobject_con', 'putobject_con', 'putobjectpart_con', 'getobject_err', 'putobject_err', 'putobjectpart_err')
        self.type = 'p'
        self.width = 3
        self.scale = 0

    def extract(self):
        global minioToken, minioEndpoint

        # get endpoint and token from /opt/vertica/config/minio.conf and mc command
        if not all(x in globals() for x in ['minioEndpoint', 'minioToken']) :
            minioEndpoint = ''
            minioToken = ''
            cmds = """
if [ -f /opt/vertica/config/minio.conf -a -f /opt/vertica/bin/mc ] ; then
  protocal="http"
  egrep -v '^\s*#' /opt/vertica/config/minio.conf | grep MINIO_VOLUMES | grep -i https && protocal=https
  egrep -v '^\s*#' /opt/vertica/config/minio.conf | grep MINIO_OPTS | grep :5433 && protocal=https

  port=""
  portListen="$(egrep -v '^\s*#' /opt/vertica/config/minio.conf | grep MINIO_OPTS \
          | grep '\-\-address' | grep ':' | awk -F ':' '{print $2}' | awk '{print $1}')"
  [ -z "${port}" -a -n "${portListen}" ] && port="${portListen}"
  if [ -z "${port}" ] ; then
    portEndpoint="$(egrep -v '^\s*#' /opt/vertica/config/minio.conf | grep MINIO_VOLUMES \
            | grep '//' | awk -F '//' '{print $2}' | grep ':' | awk -F ':' '{print $2}' | awk -F '/' '{print $1}')"
    [ -n "${portEndpoint}" ] && port="${portEndpoint}"
  fi
  [ -z "${port}" ] && port="80"

  MINIO_ACCESS_KEY="$(egrep -v '^\s*#' /opt/vertica/config/minio.conf | grep MINIO_ACCESS_KEY \
          | awk -F '=' '{print $2}' | sed -e 's/^\s*"*//g' | sed -e 's/"*\s*$//g')"
  MINIO_SECRET_KEY="$(egrep -v '^\s*#' /opt/vertica/config/minio.conf | grep MINIO_SECRET_KEY \
          | awk -F '=' '{print $2}' | sed -e 's/^\s*"*//g' | sed -e 's/"*\s*$//g')"

  export MC=/opt/vertica/bin/mc
  ${MC} config host list ddstat_test >/dev/null 2>&1 || ${MC} config host add ddstat_test ${protocal}://localhost:${port} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}  >/dev/null 2>&1
  MINIOMON_TOKEN="$(${MC} admin prometheus generate ddstat_test 2>/dev/null | grep bearer_token | cut -d : -f 2 | sed 's/ //g')"
  ${MC} config host remove ddstat_test >/dev/null 2>&1
fi
echo -n "${protocal}://localhost:${port} ${MINIOMON_TOKEN}"
            """
            ret = subprocess.check_output(['sh', '-c', cmds])
            val = ret.split(' ')
            minioEndpoint = val[0]
            minioToken = val[1]

        # query measures of Minio on current host through web RESTful service
        if minioEndpoint and minioToken :
            cmds = """
if which curl > /dev/null 2>&1 ; then
    measures="$(curl -s -H "Authorization: Bearer %s" %s/minio/prometheus/metrics 2>/dev/null | egrep -v '^#')"
    measures_con="$( grep s3_requests_current <<< "${measures}" | grep 'getobject\|putobject' \
            | awk -F '="' '{print $2}' | sed 's/"} /,/g')"
    getobject_con="$(grep getobject <<< "${measures_con}" | awk -F ',' '{print $2}')"
    putobject_con="$(grep 'putobject,' <<< "${measures_con}" | awk -F ',' '{print $2}')"
    putobjectpart_con="$(grep 'putobjectpart' <<< "${measures_con}" | awk -F ',' '{print $2}')"
    measures_err="$( grep s3_errors_total <<< "${measures}" | grep 'getobject\|putobject' \
            | awk -F '="' '{print $2}' | sed 's/"} /,/g')"
    getobject_err="$(grep getobject <<< "${measures_err}" | awk -F ',' '{print $2}')"
    putobject_err="$(grep 'putobject,' <<< "${measures_err}" | awk -F ',' '{print $2}')"
    putobjectpart_err="$(grep 'putobjectpart' <<< "${measures_err}" | awk -F ',' '{print $2}')"
fi
echo -n "${getobject_con},${putobject_con},${putobjectpart_con},${getobject_err},${putobject_err},${putobjectpart_err}"
            """ % (minioToken, minioEndpoint)
            ret = subprocess.check_output(['sh', '-c', cmds])
            val = ret.split(',')
            self.val['getobject_con'] = int(val[0]) if val[0] else 0
            self.val['putobject_con'] = int(val[1]) if val[1] else 0
            self.val['putobjectpart_con'] = int(val[2]) if val[2] else 0
            self.val['getobject_err'] = int(val[3]) if val[3] else 0
            self.val['putobject_err'] = int(val[4]) if val[4] else 0
            self.val['putobjectpart_err'] = int(val[5]) if val[5] else 0
        else :
            self.val['getobject_con'] = 0
            self.val['putobject_con'] = 0
            self.val['putobjectpart_con'] = 0
            self.val['getobject_err'] = 0
            self.val['putobject_err'] = 0
            self.val['putobjectpart_err'] = 0


dstatmodule.dstat_minio_adv = dstat_minio_adv


class dstat_minio(dstatmodule.dstat):
    """
    minio
    """

    def __init__(self):
        self.name = 'minio'
        self.nick = ('dwn', 'mem')
        self.vars = ('down', 'mem')

    def extract(self):
        cmds = """
pid="$(/usr/sbin/pidof minio)"
mem="0"; [ -n "${pid}" ] && mem="$(grep VmRSS /proc/${pid}/status \
        | awk -F ':' '{print $2}'|sed 's/[ \t]*//g')"
echo -n "$(test -n "${pid}"; echo $?),${mem}"
        """
        ret = subprocess.check_output(['sh', '-c', cmds])
        val = ret.split(',')
        self.val['down'] = long(val[0]) if val[0] else 0
        self.val['mem'] = mem_str2int(val[1]) if val[1] else 0


dstatmodule.dstat_minio = dstat_minio


class dstat_nodename(dstatmodule.dstat):
    """
    nodename output plugin. 
    """

    def __init__(self):
        self.name = 'node'
        self.nick = ('name',)
        self.vars = ('text',)
        self.type = 's'
        self.width = 12
        self.scale = 0

    def extract(self):
        self.val['text'] = ''
        if "nodeName" in globals() :
            global nodeName
            self.val['text'] = nodeName
            self.width = len(nodeName)


dstatmodule.dstat_nodename = dstat_nodename


# disable external plugins, as maybe some server install dstat package but some not.
dstatmodule.pluginpath = []


if __name__ == '__main__' :
    pass
else :
    # add dstat.Options.__repr__ function to generate constant object 
    def Options_repr (self):
        return "Options('%s')" % self.args

    dstatmodule.Options.__repr__ = Options_repr

#!/usr/bin/env python2
#encoding: utf-8
#
# Copyright (c) 2017 - 2020
# Description: cluster monitoring
# Author: DingQiang Liu

import os, sys
from optparse import OptionParser
import logging
import time
from cStringIO import StringIO
import re
from getpass import getuser

from cluster import getCluster
import util.reflection as reflection

old_stdout = sys.stdout
sys.stdout = mystdout = StringIO() 
import dstat as dstatmodule
import dstatproxy 
sys.stdout = old_stdout
srcclusterdstatmodule = reflection.overridemodule(dstatmodule, dstatproxy)

logger = logging.getLogger("clustermon")

ansi = {
    'reset': '\033[0;0m',
    'bold': '\033[1m',
    'reverse': '\033[2m',
    'underline': '\033[4m',

    'clear': '\033[2J',
    'clearline': '\033[2K',
    'save': '\033[s',
    'restore': '\033[u',
    'save_all': '\0337',
    'restore_all': '\0338',
    'linewrap': '\033[7h',
    'nolinewrap': '\033[7l',

    'up': '\033[1A',
    'down': '\033[1B',
    'right': '\033[1C',
    'left': '\033[1D',

    'default': '\033[0;0m',
}


def remotecall(src, args, nodeNamesPattern) :
    """ remotely execute script on Vertica cluster.

      Arguments:
        - src: string, python scriptlet.
        - args: dictionary of arguments for script.
        - nodeNamesPattern: regular expression pattern for select Vertica nodes.

      Returns: list of result from each nodes of Vertica cluster.
    """
    
    ret = {}
    hosts = args.pop('hosts', ['localhost'])
    user = args.pop('user', getuser())
    vc = getCluster(hosts, user)
    mch = vc.executors.remote_exec(src)
    mch.send_each(args)
    q = mch.make_receive_queue(endmarker=None)
    terminated = 0
    while 1:
      channel, result = q.get()
      if result is None :
        terminated += 1
        if terminated == len(mch):
          break
        continue
      else: 
        nodeName = channel.gateway.id
        ret.update({nodeName: result}) 

    return [ret[k] for k in [key for key in sorted(ret) if nodeNamesPattern.match(key) ]]


def initmonitor(hosts, user, nodeNamesPattern, output2csv, args) :
    """ remotely execute script on Vertica cluster.

      Arguments:
        - hosts: list of host name or IP.
        - args: list of arguments for dstat
        - nodeNamesPattern: regular expression pattern for select Vertica nodes.

      Returns: header list of ansi lines and csv lines
    """

    headers = ['', '']
    src = srcclusterdstatmodule + """
def myExit(code) :
    raise 'exitcode: ' + str(code)

if __name__ == '__channelexec__' or __name__ == '__main__' :
    global totlist, nodeName

    nodeName = channel.gateway.id.split('-')[0] # remove the tailing '-slave'

    remoteargs = channel.receive()
    args = remoteargs["args"]
    nodeName = nodeName.rjust(int(remoteargs["maxNodeNameLength"])) 
    output2csv = remoteargs["output2csv"]
    old_stdout = sys.stdout
    old_exit = sys.exit
    sys.exit = myExit
    from cStringIO import StringIO
    sys.stdout = mystdout = StringIO() 

    try :
        dstatmodule.initterm()
        dstatmodule.op = dstatmodule.Options(args)
        dstatmodule.theme = dstatmodule.set_theme()
        dstatmodule.main()

        dstatmodule.perform(0)
    except :
        channel.send([mystdout.getvalue(), ''])
    else :
        channel.send([header(totlist, totlist), csvheader(totlist) if output2csv else ''])

    sys.stdout = old_stdout
    sys.exit = old_exit
    """
    for lines in remotecall(src, {'args': args, 'maxNodeNameLength': max([len(n) for n in hosts]), 'output2csv': output2csv, 'hosts': hosts, 'user': user}, nodeNamesPattern) :
        #only get headers from 1st node
        headers = lines
        break
    
    return headers


def monitoring(update, nodeNamesPattern, output2csv) :
    """ remotely execute script on Vertica cluster.

      Arguments:
        - update: sequence number
        - nodeNamesPattern: regular expression pattern for select Vertica nodes.

      Returns: list of ansi monitoring lines and csv lines
    """

    src = """
if __name__ == '__channelexec__' or __name__ == '__main__' :
    global op, outputfile

    remoteargs = channel.receive()
    update = remoteargs["update"]
    output2csv = remoteargs["output2csv"]

    old_stdout = sys.stdout
    from cStringIO import StringIO
    sys.stdout = mystdout = StringIO() 
    old_exit = sys.exit
    sys.exit = myExit
    # DEBUG
    if output2csv :
        op.output = '/tmp/unkown.csv'
        outputfile = mycsvout = StringIO()

    try :
        dstatmodule.perform(update)
    except :
        pass
    finally :
        channel.send([mystdout.getvalue(), mycsvout.getvalue() if output2csv else ''])

    sys.stdout = old_stdout
    sys.exit = old_exit
    """
    return remotecall(src, {"update": update, 'output2csv': output2csv}, nodeNamesPattern) 


def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def myExit(code) :
    raise 'exitcode: ' + str(code)


if __name__ == "__main__":
    class MyOptionParser(OptionParser):
        def error(self, msg):
            pass

    parser = MyOptionParser()
    hostsEnv = ','.join([h for h in os.getenv('NODE_LIST', 'localhost').split(" ") if h != ''])
    parser.add_option('-H', '--hosts', type='string', dest='hostsCSV', default=hostsEnv, help='hosts name or IP seperated by comma, default is "%s"' % hostsEnv) 
    parser.add_option('-S', '--select', type='string', dest='nodeNamesExpress', default='.*', help='regular expression for select hosts to show,  default is ".*" for all hosts') 
    defaultUser = getuser()
    parser.add_option('-U', '--user', type='string', dest='user', default=defaultUser, help='os user to access the cluster, default is current user: "%s"' % defaultUser) 
    parser.add_option('--output', type='string', dest="outputFile", default=None, help='write CSV output to file') 
    parser.usage = ""

    helpArgs = ['-h', '--help', '--list']
    if [ a for a in sys.argv[1:] if a in helpArgs] :  
        # hack for replace help info
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO() 
        old_exit = sys.exit 

        try :
            dstatmodule.initterm()
            dstatmodule.Options([ a for a in sys.argv[1:] if a in helpArgs ])
        except :
            pass

        if not '--list' in sys.argv[1:] :
            parser.remove_option('--output')
            parser.print_help()
        
        sys.stdout = old_stdout
        sys.exit = old_exit
        print(mystdout.getvalue().replace('dstat', 'ddstat').replace('Options:', 'Additional options:'))
        exit(0)

    args = ["--time", "--nodename"]
    needAll = True
    noColor = False
    noHeaders = False
    skipnext = False
    for arg in sys.argv[1:] :
        if arg in ['-H', '--hosts', '-U', '--user', '-S', '--select', '--output', '-t', '--time', '--nodename', '--color', '--nocolor', '--noheaders', '--noupdate']:
            if arg == '--color' : 
                noColor = False
            if arg == '--nocolor' : 
                noColor = True
            if arg == '--noheaders' : 
                noHeaders = True
            if arg in ['-H', '--hosts', '-U', '--user', '-S', '--select', '--output']:
                skipnext = True
            continue

        if skipnext :
            skipnext = False
        else :
            args.append(arg)
            if arg[0] == '-'and len(arg) > 1 and arg not in ['--bits', '--float', '--integer', '--bw', '--black-on-white', '--output', '--profile']:
                needAll = False

    delay = 1
    count = -1
    if len(args) >= 1 :
        last1 = args[-1]
        last2 = ''
        if len(args) >= 2 :
            last2 = args[-2]
        if RepresentsInt(last2) and RepresentsInt(last1):
            delay = int(last2)
            count = int(last1)
            args = args[:-2]
        elif RepresentsInt(last1):
            delay = int(last1)
            args = args[:-1]
    if delay <= 0 :
        delay = 1

    if needAll :
        args = args + ['--all'] 
    if not noColor :
        args = args + ['--color'] 
    args = args + ['--noheaders', '--noupdate', str(delay), '0'] # '--noupdate' should be the lastest parameter

    (options, _) = parser.parse_args()
    hosts = options.hostsCSV.split(',')
    nodeNamesPattern = re.compile(options.nodeNamesExpress)

    outputfile = None

    try:
        # init, get headers
        headers = initmonitor(hosts, options.user, nodeNamesPattern, not options.outputFile is None, args)
        if 'not recognized' in headers[0]:
            print(headers[0].replace('dstat', 'ddstat'))
            exit(1)

        newFile = True
        if options.outputFile :
            if os.path.exists(options.outputFile) :
                outputfile = open(options.outputFile, 'a', 0)
                newFile = False
            else :
                outputfile = open(options.outputFile, 'w', 0)
    
        # get counters
        UPDATE_BEGIN = 1000 # Seems there will be weird issue if update increase from 1
        update = UPDATE_BEGIN 
        sys.stdout.write(ansi['nolinewrap'])
        while (count != 0) :
            if not noHeaders :
                sys.stdout.write(headers[0])
                if outputfile and newFile and update == UPDATE_BEGIN :
                    outputfile.write(headers[1])
            for lines in monitoring(update, nodeNamesPattern, not options.outputFile is None) :
                sys.stdout.write(lines[0])
                # TODO: average line
                if outputfile :
                    outputfile.write(lines[1])

            update += 1
            if update < 0 :
                update = UPDATE_BEGIN + 1
            if (count > 0) and (update - UPDATE_BEGIN >= count) :
                break
            time.sleep(delay)

    except KeyboardInterrupt :
        pass
    finally :
        if outputfile :
            outputfile.flush()
            outputfile.close()

    sys.stdout.write(ansi['reset'])
    sys.stdout.write('\r')
    sys.stdout.flush()
    exit(0)


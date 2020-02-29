#!/usr/bin/python
#
# Copyright (c) 2006 - 2017, Hewlett-Packard Development Co., L.P. 
# Description: Vertica cluster communication and configuration
# Author: DingQiang Liu

import sys
import os, atexit
import socket
from multiprocessing.dummy import Pool as ThreadPool
from functools import partial
import re
from ConfigParser import ConfigParser
import logging

import execnet


logger = logging.getLogger(__name__)


def getCluster(hosts, user):
  """
  single instance of Cluster
    Arguments:
      hosts: list of host name or IP.
  """
  global __g_Cluster
  
  try:
    if len(__g_Cluster.executors) == 0 :
      __g_Cluster = None
    return __g_Cluster
  except NameError:
    __g_Cluster = Cluster(hosts, user)
    if len(__g_Cluster.executors) == 0 :
      msg = "cluster is not accessible! You can not access newest info of Vertica."
      print "ERROR: %s" % msg
      logger.error(msg)

      __g_Cluster = None
    else :
      # close Cluster automatically when exiting
      atexit.register(destroyCluster)

  return __g_Cluster



def destroyCluster():
  """
  close Cluster
  """
  global __g_Cluster

  try:
    if not __g_Cluster is None :
        __g_Cluster.destroy()
  except NameError:
    pass

  __g_Cluster = None



class Cluster:
  def __init__(self, hosts, user):
    """ Register datacollectors of Vertica
    Arguments:
      hosts: list of host name or IP.
    """

    self.hosts = hosts
    self.user = user

    self.executors = execnet.Group()

    # create executors in parallel
    self.initExecutersParallel()

    
  def initExecutersParallel(self) :
    pool = ThreadPool()
    gws = pool.map(self.createExecuter, range(len(self.hosts)))
    pool.close()
    pool.join()
    for gw in gws :
      if not gw is None:
        self.executors._register(gw)
    

  def createExecuter(self, i) :
    gw = None
    s = socket.socket()
    try:
      # check connectivity 
      s.settimeout(3)
      s.connect((self.hosts[i], 22)) 
    
      tg = execnet.Group()
      pythonPath = '/usr/bin/python2' # Note: other server maybe has different installation location than sys.executable, just use default.
      gw = tg.makegateway("ssh=%s@%s//id=%s//python=%s" % (self.user, self.hosts[i], self.hosts[i], pythonPath))      
      tg._unregister(gw)
      del gw._group
    except Exception: 
      msg = 'ssh port 22 of server "%s" with user "%s" is not accessible! Ignore it, but you can not access newest info of this node.' % (self.hosts[i], self.user) 
      print '\nERROR: %s' % msg
      logger.exception(msg)
    finally:
      s.close()

    return gw


  def destroy(self):
    if not self.executors is None :
      self.executors.terminate()
      self.executors = None


# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module to manage load information of Compute Engine instances."""



import logging
import random

from google.appengine.api import memcache
from google.appengine.ext import db


class SingleInstance(db.Model):
  """Datastore schema to represent single instance.

  Instance information in Datastore works as back up in case table in Memcache
  is gone.
  """
  ip_address = db.StringProperty(multiline=False)
  statusresp = db.TextProperty()

  @classmethod
  def GetByName(cls, name):
    """Utility to get SingleInstance object in Datastore.

    Args:
      name: Name of the instance.
    Returns:
      SingleInstance object saved in Datastore.  None if the name is not found.
    """
    return cls.get_by_key_name(name)
    
class SingleServer(db.Model):
  ip_address = db.StringProperty(multiline=False)
  port = db.StringProperty(multiline=False)
  statusresp = db.TextProperty()
  gridstr = db.StringProperty(multiline=False)
  
  @classmethod
  def GetByName(cls, name):
    return cls.get_by_key_name(name)


class LoadInfo(object):
  """Utility class to handle load information database.

  Memcache holds list of instances with load information.
  Key: Name of instance.
  Value: Dictionary with the following keys.
    ip_address: IP address in string
    load: Load level in integer [0-100].
    force: Boolean to indicate it's set by admin UI.
  Instance name is generated with UUID when the instance is created.
  List of all keys are saved with under 'all_instances' key, in order to
  retrieve information of all instances.
  """
  SERVER_INFO_PREFIX = "server-"
  INSTANCE_INFO_PREFIX = "instance-"
  
  ALL_SERVERS = 'all_servers'
  
  ALL_INSTANCES = 'all_instances'
  IP_ADDRESS = 'ip_address'
  PORT = 'port'
  STATUS = 'status'
  STATUS_NONE = 'none'
  STATUS_LOADING = 'loading'
  STATUS_UP = 'up'
  LAST_RESP = 'last_resp'
  LOAD = 'load'
  NUM_PLAYERS = 'num_players'
  FORCE = 'force'
  CANDIDATE_MIN_SIZE = 3

  @classmethod
  def _GetInstanceList(cls):
    """Returns all instance names in list."""
    all_instances = memcache.get(cls.ALL_INSTANCES)
    if all_instances is not None:
      return all_instances
    all_instances = [key.name() for key in SingleInstance.all(keys_only=True)]
    memcache.set(cls.ALL_INSTANCES, all_instances)
    return all_instances
    
  @classmethod
  def _GetServerList(cls):
    all_servers = memcache.get(cls.ALL_SERVERS)
    if all_servers is not None:
      return all_servers
    all_servers = [key.name() for key in SingleServer.all(keys_only=True)]
    memcache.set(cls.ALL_SERVERS, all_servers)
    return all_servers

  @classmethod
  def _IsManagedInstance(cls, name):
    """Determines whether the instance is managed by this application.

    Args:
      name: Name of the instance to check.
    Returns:
      Boolean value.
    """
    return name in cls._GetInstanceList()
  
  @classmethod
  def IsManagedServer(cls, grid):
    return grid in cls._GetServerList()

  @classmethod
  def InitializeTable(cls):
    """Clears list of managed instances and initializes the load table."""
    memcache.set(cls.ALL_INSTANCES, [])
    memcache.set(cls.ALL_SERVERS, [])

  @classmethod
  def AddInstance(cls, name, resp):
    """Adds new instance to the list of instances in Memcache.

    Args:
      name: Name of the instance.
    """
    # First, update Datastore.
    # Add StringInstance for this instance without ip_address property.
    # Existing entity with the same name is overwritten by put() call.
    newins = SingleInstance(key_name=name)
    newins.statusresp = str(resp)
    newins.put()

    # Then update Memcache.
    # To avoid race condition, use cas update.
    memcache_client = memcache.Client()
    while True:
      instances = memcache_client.gets(cls.ALL_INSTANCES)
      if instances is None:
        # This is not supposed to happen, since InitializeTable() is
        # supposed to be called in advance at cluster set up.
        # This is dangerous operation, since somebody else might have already
        # set value betweeen previous gets() and now.
        logging.error('all_instances entry in Memcache is None.')
        memcache.set(cls.ALL_INSTANCES, [name])
        break
      if name in instances:
        break
      instances.append(name)
      if memcache_client.cas(cls.ALL_INSTANCES, instances):
        break
    
    info = {cls.STATUS: cls.STATUS_LOADING, cls.LAST_RESP: str(resp)}
    memcache.set(cls.INSTANCE_INFO_PREFIX+name, info)
  
  @classmethod
  def AddServer(cls, grid, resp):
    newserv = SingleServer(key_name = grid)
    newserv.gridstr = grid
    newserv.statusresp = str(resp)
    newserv.put()
    
    memcache_client = memcache.Client()
    while True:
      servers = memcache_client.gets(cls.ALL_SERVERS)
      if servers is None:
        logging.error('all_servers entry in Memcache is None.')
        memcache.set(cls.ALL_SERVERS, [grid])
        break
      if grid in servers:
        logging.error('adding same server twice!')
        break
      servers.append(grid)
      if memcache_client.cas(cls.ALL_SERVERS, servers):
        break
    
    info = {cls.STATUS: cls.STATUS_LOADING, cls.LAST_RESP: str(resp)}
    memcache.set(cls.SERVER_INFO_PREFIX+grid, info)

  @classmethod
  def RegisterInstanceIpAddress(cls, name, ip_address):
    """Registers IP address of the instance to load information.

    If the instance is not in the list of instances the application manages,
    the function does nothing.

    Args:
      name: Name of the instance.
      ip_address: IP address in string format.
    """
    if cls._IsManagedInstance(name):
      # Record IP address to SingleInstance in Datastore.
      instance = SingleInstance.GetByName(name)
      instance.ip_address = ip_address
      instance.put()
      memcache.set(cls.INSTANCE_INFO_PREFIX+name, {cls.IP_ADDRESS: ip_address, cls.STATUS: cls.STATUS_UP})
        
    else:
      #cls.AddInstance(name)
      #cls.RegisterInstanceIpAddress(name, ip_address)
      logging.error('Registration request for unmanaged instance %s', name)
    
    
      
  @classmethod
  def RegisterServerAddress(cls, grid, ip_address, port):
    if cls.IsManagedServer(grid):
      server = SingleServer.GetByName(grid)
      server.ip_address = ip_address
      server.port = port
      server.put()
      memcache.set(cls.SERVER_INFO_PREFIX+grid, {cls.IP_ADDRESS: ip_address, cls.PORT: port, cls.STATUS: cls.STATUS_UP})
    else:
      logging.error('Registration request for unmanaged server %s', grid)

  @classmethod
  def RemoveInstance(cls, name):
    """Removes load information entry of the instance.

    Args:
      name: Name of the instance to remove from load information list.
    """
    # Use cas operation to remove from instance name list.
    memcache_client = memcache.Client()
    while True:
      instances = memcache_client.gets(cls.ALL_INSTANCES)
      if not instances:
        break
      try:
        instances.remove(name)
      except ValueError:
        # The instance name was not in the list.
        break
      if memcache_client.cas(cls.ALL_INSTANCES, instances):
        break

    # Delete the entry for the instance in Memcache and Datastore.
    datastore_single_instance = SingleInstance.GetByName(name)
    if datastore_single_instance:
      memcache.delete(cls.INSTANCE_INFO_PREFIX+name)
      datastore_single_instance.delete()
    else:
      logging.error('Trying to remove instance with no datastore entry %s', name)
      
  @classmethod
  def RemoveServer(cls, grid):
    memcache_client = memcache.Client()
    while True:
      servers = memcache_client.gets(cls.ALL_SERVERS)
      if not servers:
        break
      try:
        servers.remove(grid)
      except ValueError:
        logging.error('Attempted to remove server that does not exist %s', grid)
        break
      if memcache_client.cas(cls.ALL_SERVERS, servers):
        break
    
    datastore_single_server = SingleServer.GetByName(grid)
    if datastore_single_server:
      memcache.delete(cls.SERVER_INFO_PREFIX+grid)
      datastore_single_server.delete()
    else:
      logging.error('Trying to remove server with no datastore entry %s', grid)
      
  @classmethod
  def RemoveAllInstancesAndServers(cls):
    """Removes load information entry of all instances during teardown.
    """
    # Use cas operation to remove all instances from instance list
    memcache_client = memcache.Client()
    while True:
      if memcache_client.flush_all():
        break

    # Delete the entries for the instances in Memcache and Datastore.
    while True:
      datastore_all_instances = SingleInstance.all()
      allinstances = datastore_all_instances.fetch(limit=100)
      if len(allinstances) == 0:
        break
      for ins in allinstances:
        ins.delete()
        
    while True:
      datastore_all_servers = SingleServer.all()
      allservers = datastore_all_servers.fetch(limit=100)
      if len(allservers) == 0:
        break
      for serv in allservers:
        serv.delete()
  
  
  @classmethod
  def UpdateInstanceLoadInfo(cls, name, load):
    if not cls._IsManagedInstance(name):
      return False

    info = memcache.get(cls.INSTANCE_INFO_PREFIX+name)
    if not info:
      # The entry for this instance doesn't exist in Memcache.
      logging.warning('Load entry of instance %s does not exist in Memcache',
                      name)
      # Try to get from Datastore.
      ds_instance = SingleInstance.GetByName(name)
      if ds_instance:
        info = {cls.STATUS: cls.STATUS_UP, cls.IP_ADDRESS: ds_instance.ip_address}
      else:
        logging.error('Load entry for instance %s not found in Datastore',
                      name)
        return False

    info[cls.LOAD] = load
    return memcache.set(cls.INSTANCE_INFO_PREFIX+name, info)
    
  @classmethod
  def UpdateServerNumPlayers(cls, grid, num):
    if not cls.IsManagedServer(grid):
      return False
    
    info = memcache.get(cls.SERVER_INFO_PREFIX+grid)
    if not info:
      logging.warning('Load entry of server %s does not exist in Memcache', grid)
      ds_server = SingleServer.GetByName(grid)
      if ds_server:
        info = {cls.STATUS: cls.STATUS_UP, cls.IP_ADDRESS: ds_server.ip_address, cls.PORT: ds_server.port}
      else:
        logging.error('Load entry for server %s not found in Datastore', grid)
        return False
    
    info[cls.NUM_PLAYERS] = num
    return memcache.set(cls.SERVER_INFO_PREFIX+grid, info)
    
  @classmethod
  def GetInstanceLoadInfo(cls, name):
    if not cls._IsManagedInstance(name):
      logging.error('Load request being sent for unregistered instance %s', name)
      return False
    info = memcache.get(cls.INSTANCE_INFO_PREFIX+name)
    if info:
      return info
    else:
      # Try to get from Datastore.
      ds_instance = SingleInstance.GetByName(name)
      if ds_instance:
        if (ds_instance.ip_address is None) or (not ('.' in ds_instance.ip_address)): # Not self-registered yet
          info = {cls.STATUS: cls.STATUS_LOADING, cls.LAST_RESP: ds_instance.statusresp}
        else: #Self-registered
          info = {cls.STATUS: cls.STATUS_UP, cls.IP_ADDRESS: ds_instance.ip_address}
      else: # Doesn't exist
        return {cls.STATUS: cls.STATUS_NONE}
    memcache.set(cls.INSTANCE_INFO_PREFIX+name, info)
    return info
  
  @classmethod
  def GetServerLoadInfo(cls, grid):
    if not cls.IsManagedServer(grid):
      logging.info('Load request being sent for unregistered server %s', grid)
      return False
    info = memcache.get(cls.SERVER_INFO_PREFIX+grid)
    if info:
      return info
    else:
      server = SingleServer.GetByName(grid)
      if server:
        if (server.ip_address is None) or (not ('.' in server.ip_address)):
          info = {cls.STATUS: cls.STATUS_LOADING, cls.LAST_RESP:server.statusresp}
        else:
          info = {cls.STATUS: cls.STATUS_UP, cls.IP_ADDRESS: server.ip_address, cls.PORT: server.port}
      else:
        logging.error("Server doesn't exist, but is shown as managed: %s", grid)
        return False
    memcache.set(cls.SERVER_INFO_PREFIX+grid, info)
    return info

  @classmethod
  def GetAllInstances(cls):
    all_instances = cls._GetInstanceList()
    if not all_instances:
      return {}
    all_instances_pre = [cls.INSTANCE_INFO_PREFIX+name for name in all_instances]
    return memcache.get_multi(all_instances_pre)

  @classmethod
  def GetIdleInstance(cls):
    all_infos = cls.GetAllInstances()
    candidates = []
    # At least CANDIDATE_MIN_SIZE instances are added to candidates.
    # After that, if the instance's load is the same as the last candidate's
    # load, the instance is added to candidates.
    for info in sorted(all_infos.values(),
                       key=lambda x: x.get(cls.LOAD, 10000)):
      if cls.LOAD not in info:
        break
      if len(candidates) < cls.CANDIDATE_MIN_SIZE:
        candidates.append(info)
        last_load = info[cls.LOAD]
      else:
        if info[cls.LOAD] == last_load:
          candidates.append(info)
        else:
          break
    # If candidates are empty, we cannot return anything.
    if not candidates:
      return None
    # Return IP address of one of the candidates randomly.
    return candidates[random.randint(0, len(candidates) - 1)]

  @classmethod
  def GetAverageLoad(cls):
    """Calculates average load of all instances.
    Returns:
      Cluster size and average load.  
    """
    all_infos = cls.GetAllInstances()
    total_load = 0
    cluster_size = 0
    for info in all_infos.values():
      if cls.LOAD in info:
        cluster_size += 1
        total_load += info[cls.LOAD]
    if not cluster_size:
      return 0, 0
    return cluster_size, total_load / cluster_size
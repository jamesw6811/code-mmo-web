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
  gridstr = db.StringProperty(multiline=False)

  @classmethod
  def GetByName(cls, name):
    """Utility to get SingleInstance object in Datastore.

    Args:
      name: Name of the instance.
    Returns:
      SingleInstance object saved in Datastore.  None if the name is not found.
    """
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

  ALL_INSTANCES = 'all_instances'
  IP_ADDRESS = 'ip_address'
  STATUS = 'status'
  STATUS_NONE = 'none'
  STATUS_LOADING = 'loading'
  STATUS_UP = 'up'
  LOAD = 'load'
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
  def _IsManagedInstance(cls, name):
    """Determines whether the instance is managed by this application.

    Args:
      name: Name of the instance to check.
    Returns:
      Boolean value.
    """
    return name in cls._GetInstanceList()

  @classmethod
  def InitializeTable(cls):
    """Clears list of managed instances and initializes the load table."""
    memcache.set(cls.ALL_INSTANCES, [])

  @classmethod
  def AddInstance(cls, name, grid):
    """Adds new instance to the list of instances in Memcache.

    Args:
      name: Name of the instance.
    """
    # First, update Datastore.
    # Add StringInstance for this instance without ip_address property.
    # Existing entity with the same name is overwritten by put() call.
    newins = SingleInstance(key_name=name);
    newins.gridstr = grid;
    newins.put();

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
      grid = instance.gridstr;
      instance.put()
      # Update Memcache information.
      memcache.set(grid, {cls.IP_ADDRESS: ip_address, cls.STATUS: cls.STATUS_UP})
      return instance.gridstr
    else:
      #cls.AddInstance(name)
      #cls.RegisterInstanceIpAddress(name, ip_address)
      logging.error('Registration request for unmanaged instance %s', name)

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
      grid = datastore_single_instance.gridstr
      memcache.delete(grid)
      datastore_single_instance.delete()
    else:
      logging.error('Trying to remove instance with no datastore entry!')
      
  @classmethod
  def RemoveAllInstances(cls):
    """Removes load information entry of all instances during teardown.

    Args:
      name: Name of the instance to remove from load information list.
    """
    # Use cas operation to remove all instances from instance list
    memcache_client = memcache.Client()
    while True:
      if memcache_client.flush_all():
        break

    # Delete the entries for the instances in Memcache and Datastore.
    while True:
      datastore_all_instances = SingleInstance.all();
      allinstances = datastore_all_instances.fetch(limit=100)
      if len(allinstances) == 0:
        break
      for ins in allinstances:
        ins.delete()
      

  @classmethod
  def requestLoadInfo(cls, name, grid):
    # TODO uncomment below for security
    #if not cls._IsManagedInstance(name):
   #   logging.error('Load request being sent from unregistered server.')
    #  return False
    info = memcache.get(grid)
    if info:
      return info;
    else:
      # Try to get from Datastore.
      gridq = SingleInstance.all().filter("gridstr =", grid)
      gridqr = gridq.fetch(limit = 2)
      ds_instance = None;
      if len(gridqr) > 1:
        logging.error('More than one server registered on same grid position!')
        return False
      elif len(gridqr) > 0:
        ds_instance = gridqr[0]
      else:
        ds_instance = None
        
      if ds_instance:
        try:
          info = {cls.STATUS: cls.STATUS_UP, cls.IP_ADDRESS: ds_instance.ip_address}
          if (ds_instance.ip_address is None) or (not ('.' in ds_instance.ip_address)):
            raise AttributeError("No IP Address.")
        except AttributeError:
          logging.info('No IP address attribute.')
          info = {cls.STATUS: cls.STATUS_LOADING}
      else:
        return {cls.STATUS: cls.STATUS_NONE}

    memcache.set(grid, info)
    return info

  @classmethod
  def getInstanceIpAddress(cls, grid):
    info = memcache.get(grid)
    if info:
      if info[cls.STATUS] == cls.STATUS_UP:
        return info[cls.IP_ADDRESS]
      else:
        return ''
    else:
      # Try to get from Datastore.
      gridq = SingleInstance.all().filter("gridstr =", grid)
      gridqr = gridq.run(limit = 5)
      ds_instance = None;
      if len(gridqr) > 1:
        logging.error('More than one server registered on same grid position!')
        return ''
      elif len(gridqr) > 0:
        ds_instance = gridqr[0]
      else:
        ds_instance = None
        
      if ds_instance:
        try:
          info = {cls.STATUS: STATUS_UP, cls.IP_ADDRESS: ds_instance.ip_address}
        except AttributeError:
          logging.info('No IP address attribute in getIP.')
          return ''
      else:
        return ''
    memcache.set(grid, info)
    return info[cls.IP_ADDRESS]



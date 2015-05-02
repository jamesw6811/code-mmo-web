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

"""Module to manipulate Compute Engine instances as game backend servers.

This module uses Google APIs Client Library to control Compute Engine.

  http://code.google.com/p/google-api-python-client/

"""



import logging
import os
import uuid
import ast

from apiclient.discovery import build
from apiclient.errors import HttpError
import httplib2
from urllib import urlencode
import jinja2
from oauth2client.client import OAuth2Credentials

from load_info import LoadInfo

from google.appengine.api import app_identity
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class AuthorizedUserId(db.Model):
  """Datastore schema to hold authorized user ID."""
  user_id = db.StringProperty(multiline=False)
  credentials = db.TextProperty()


class ComputeEngineController(object):
  """Class to manipulate Compute Engine instances.

  This class uses Google Client API module to manipulate Compute Engine.

  Attributes:
    compute_api: Client API object with authorized HTTP.
  """

  SCOPE = 'https://www.googleapis.com/auth/compute'

  PROJECT_ID = 'subtle-palisade-726'
  CLOUD_STORAGE_DIR = 'gs://codemmo-source'

  COMPUTE_API_VERSION = 'v1'
  DEFAULT_ZONE = 'us-central1-a'
  DEFAULT_IMAGE = 'debian-7-wheezy-v20140926'
  DEFAULT_IMAGE_PROJECT = 'debian-cloud'

  DEFAULT_MACHINE_TYPE = 'n1-standard-1'

  INITIAL_CLUSTER_SIZE = 1
  API_URL_BASE = ('https://www.googleapis.com/compute/%s/projects/' %
                  COMPUTE_API_VERSION)
  WORKER_NAME_PREFIX = 'gameserver-'
  USER_ID_KEY = 'userid'
  USER_CREDENTIALS_KEY = 'user_credentials'
  
  INSTANCE_MANAGER_PORT = '10000' # Port to use to connect to instance's manager once it is started
  INSTANCE_MANAGER_ADDSERVER = "addserver" # Endpoint for adding a new server

  def __init__(self, credentials=None):
    """Initialize Client API object for Compute Engine manipulation.

    If authorized HTTP is not given by parameter, it uses user ID stored
    in Memcache and fetches credentials for that user.

    Args:
      credentials: OAuth2 credentials of current user.
    """
    if credentials:
      user_id = users.get_current_user().user_id()
      credentials_in_json = credentials.to_json()
      authorized_user = AuthorizedUserId.get_or_insert(
          self.USER_ID_KEY, user_id=user_id,
          credentials=db.Text(credentials_in_json))
      memcache.set(self.USER_CREDENTIALS_KEY, credentials_in_json)
      if (authorized_user.user_id != user_id or
          str(authorized_user.credentials) != credentials_in_json):
        authorized_user.user_id = user_id
        authorized_user.credentials = db.Text(credentials_in_json)
        authorized_user.put()
    else:
      credentials_in_json = memcache.get(self.USER_CREDENTIALS_KEY)
      if not credentials_in_json:
        authorized_user = AuthorizedUserId.get_by_key_name(self.USER_ID_KEY)
        credentials_in_json = str(authorized_user.credentials)
      credentials = OAuth2Credentials.from_json(credentials_in_json)
    self.compute_api = build('compute', self.COMPUTE_API_VERSION,
                             http=credentials.authorize(httplib2.Http()))

  def _ApiUrl(self, project='', paths=(), is_global=False):
    """Returns API path for the specified resource.

    Args:
      project: Project name.  If unspecified, the default project name is used.
      paths: List or tuple of names to indicate the path to the resource.
      is_global: Boolean to indicate whether the resource is global.
    Returns:
      API path to the specified resource in string.
    """
    if not project:
      project = self.PROJECT_ID

    if is_global:
      return self.API_URL_BASE + project + '/global/' + '/'.join(paths)
    else:
      return self.API_URL_BASE + project + '/' + '/'.join(paths)
  
  def _StartInstance(self, instance_name):
    """Creates Compute Engine instance with the given name."""
    logging.info('Starting instance: ' + instance_name)

    startup_script_template = jinja_environment.get_template(
        os.path.join('worker', 'checkload.py'))
    startup_script = startup_script_template.render({
        'hostname': app_identity.get_default_version_hostname()
        })

    diskparam = {

    }

    param = {
        'kind': 'compute#instance',
        'name': instance_name,
        'zone': self._ApiUrl(paths=['zones', self.DEFAULT_ZONE]),
        'machineType': self._ApiUrl(
            paths=['zones', self.DEFAULT_ZONE,
                   'machineTypes', self.DEFAULT_MACHINE_TYPE]),
        'disks': [{
                    'autoDelete': 'true',
                    'boot': 'true',
                    'type': 'PERSISTENT',
                    'initializeParams' : {
                      'diskName': instance_name,
                      'sourceImage': self._ApiUrl(self.DEFAULT_IMAGE_PROJECT,
                              paths=['images', self.DEFAULT_IMAGE],
                              is_global=True)
                    }
        }],
        'networkInterfaces': [
            {
                'kind': 'compute#networkInterface',
                'network': self._ApiUrl(paths=['networks', 'default'],
                                        is_global=True),
                'accessConfigs': [
                    {
                        'type': 'ONE_TO_ONE_NAT',
                        'name': 'External NAT'
                    }
                ],
            }
        ],
        'serviceAccounts': [
            {
                'kind': 'compute#serviceAccount',
                'email': 'default',
                'scopes': [
                    'https://www.googleapis.com/auth/devstorage.read_only',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/datastore'
                ]
            }
        ],
        'metadata': {
            'items': [
                {
                    'key': 'startup-script',
                    'value': startup_script,
                },
            ],
        }
    }

    logging.info('Create instance with parameter: %s', str(param))

    operation = self.compute_api.instances().insert(
        project=self.PROJECT_ID, zone=self.DEFAULT_ZONE, body=param).execute()

    
    logging.info('Create instance response: %s', str(operation))
    return operation

  def checkResponse(self, response):
    """Returns the operation status for the given operation."""
    response = ast.literal_eval(response);
    gce_service = self.compute_api
    status = response['status']
    operation_id = response['name']

    # Identify if this is a per-zone resource
    if 'zone' in response:
      zone_name = response['zone'].split('/')[-1]
      request = gce_service.zoneOperations().get(
          project=self.PROJECT_ID,
          operation=operation_id,
          zone=zone_name)
    else:
      request = gce_service.globalOperations().get(
           project=self.PROJECT_ID, operation=operation_id)

    response = request.execute()
    if response:
      status = response['status']
    return response

  def DeleteInstance(self, instance_name):
    """Stops and deletes the instance specified by the name."""
    logging.info('Deleting instance %s', instance_name)
    LoadInfo.RemoveInstance(instance_name)
    result = self.compute_api.instances().delete(
        project=self.PROJECT_ID, zone=self.DEFAULT_ZONE,
        instance=instance_name).execute()
    logging.info(str(result))

  def GetInstanceInfo(self, instance_name):
    """Retrieves instance information.

    The detail of returned structure is described here.
      https://google-api-client-libraries.appspot.com/documentation/compute/v1beta13/python/latest/compute_v1beta13.instances.html#get

    Args:
      instance_name: Name of the instance.
    Returns:
      Dictionary that contains Compute Engine instance information.
      None if the information of the instance cannot be retrieved.
    """
    try:
      return self.compute_api.instances().get(
          project=self.PROJECT_ID, zone=self.DEFAULT_ZONE,
          instance=instance_name).execute()
    except HttpError, e:
      logging.error('Failed to get instance information of %s', instance_name)
      logging.error(e)
    return None

  def ListInstances(self):
    """Returns list of instance names managed by this application.

    Returns:
      List of instance names (string).  If there's no instance, returns
      empty list.
    """
    instance_list = []
    page_token = None
    try:
      while True:
        response = self.compute_api.instances().list(
            project=self.PROJECT_ID, zone=self.DEFAULT_ZONE,
            pageToken=page_token,
            filter='name eq ^{0}.+'.format(self.WORKER_NAME_PREFIX)).execute()
        if response and 'items' in response:
          instance_list.extend(response.get('items', []))
        else:
          break
        page_token = response.get('nextPageToken')
        if not page_token:
          break
    except HttpError, e:
      logging.error('Failed to retrieve Compute Engine instance list: %s',
                    str(e))

    return instance_list

  def StartUpCluster(self):
    LoadInfo.InitializeTable()
    self.IncreaseEngine()
    
  def AddServer(self, grid):
    # If current instance has open room, use it
    idle_instance = LoadInfo.GetIdleInstance()
    if not (idle_instance == None):
      ip_address = idle_instance[LoadInfo.IP_ADDRESS]
      
      # Send request to server manager to create new server
      h = httplib2.Http()
      data = {"grid" : grid};
      resp, content = h.request("http://"+ip_address+":"+self.INSTANCE_MANAGER_PORT+"/"+self.INSTANCE_MANAGER_ADDSERVER, "POST", urlencode(data))
      
      # Track new server 
      LoadInfo.AddServer(grid, resp)
      
      # Re-assess load
      self.assessLoad()
    else: # Otherwise, start new instance
      logging.error('Attempting to add server %s, but no idle instances!', grid)
      
  def RemoveServer(self, grid):
    # TODO: Maybe confirm with server manager that actual process is ended in case servers need to be force-quit
    LoadInfo.RemoveServer(grid)

  def TearDownCluster(self):
    for instance in self.ListInstances():
      self.DeleteInstance(instance['name'])

  def IncreaseEngine(self):
    instance_name = self.WORKER_NAME_PREFIX + str(uuid.uuid4())
    response = self._StartInstance(instance_name)
    LoadInfo.AddInstance(instance_name, response)

  def DecreaseEngine(self, decrease_count):
    # This is the placeholder for user's implementation.
    pass
  
  def assessLoad(self):
    pass # Assess current load and remove instances with no load
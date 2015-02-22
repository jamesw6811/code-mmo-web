import logging
import os

import jinja2
from oauth2client.anyjson import simplejson as json
from oauth2client.appengine import OAuth2Decorator
from oauth2client.client import AccessTokenRefreshError
import webapp2

from compute_engine_controller import ComputeEngineController
from load_info import LoadInfo

from google.appengine.ext import db
from google.appengine.api import app_identity


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader('worker'))


decorator = OAuth2Decorator(
    client_id = '996450208987-9259qcm3a6qh8ch15nsf6tpb0jrk2knu.apps.googleusercontent.com',
    client_secret = 'DPcR1rc9oZwBBuf6fzgj231a',
    scope=ComputeEngineController.SCOPE)


class IpAddressRequestLog(db.Model):
  """Datastore schema for game server IP address retrieval log."""
  client_ip = db.StringProperty()
  server_ip = db.StringProperty()
  timestamp = db.DateTimeProperty(auto_now=True)


class FrontendHandler(webapp2.RequestHandler):
  """URL handler class for IP address request."""

  def get(self):
    """Returns an available server's IP address in JSON format."""
    ip = LoadInfo.getInstanceIpAddress("0,0")
    if not ip:
      ip = ''
    self.response.out.write(json.dumps({'ipaddress': ip}))
    IpAddressRequestLog(client_ip=self.request.remote_addr,
                        server_ip=ip).put()


class AdminUiHandler(webapp2.RequestHandler):
  """URL handler class for admin UI page."""

  @decorator.oauth_required
  def get(self):
    """Returns admin UI of game server cluster."""
    try:
      ComputeEngineController(decorator.credentials)
      # This handler returns stats.html as is.  We still need handler here
      # to take care of OAuth2.
      html_path = os.path.join(os.path.dirname(__file__),
                               'static_files', 'stats.html')

      self.response.out.write(open(html_path).read())
    except AccessTokenRefreshError:
      self.redirect(decorator.authorize_url())


class StatsJsonHandler(webapp2.RequestHandler):
  """URL handler class for stats list of the cluster."""

  @decorator.oauth_required
  def get(self):
    """Returns stats of managed Compute Engine instances for Admin UI."""
    load_entries = []
    instance_list = ComputeEngineController(
        decorator.credentials).ListInstances()
    all_load_info = LoadInfo.GetAll()

    # First, list managed instances whose Compute Engine status is found.
    for instance in instance_list:
      instance_name = instance['name']
      if instance_name in all_load_info:
        info = all_load_info[instance_name]
        load_entries.append({
            'host': instance_name,
            'ipaddress': info.get(LoadInfo.IP_ADDRESS, ''),
            'status': instance['status'],
            'load': info.get(LoadInfo.LOAD, 0),
            'force_set': info.get(LoadInfo.FORCE, False),
        })
        del all_load_info[instance_name]

    # Then, list managed instances without Compute Engine status.
    for name, info in all_load_info.items():
      load_entries.append({
          'host': name,
          'ipaddress': info.get(LoadInfo.IP_ADDRESS, ''),
          'status': 'NOT FOUND',
          'load': info.get(LoadInfo.LOAD, 0),
          'force_set': info.get(LoadInfo.FORCE, False),
      })

    self.response.out.write(json.dumps(load_entries))


class StatsUserJsonHandler(webapp2.RequestHandler):
  """URL handler class for game server list of the cluster."""

  def get(self):
    """Returns stats of game instances for non logged-in users."""
    load_entries = []
    all_load_info = LoadInfo.GetAll()

    for name, info in all_load_info.items():
      load_entries.append({
          'host': name,
          'ipaddress': info.get(LoadInfo.IP_ADDRESS, ''),
          'load': info.get(LoadInfo.LOAD, 0),
      })

    self.response.out.write(json.dumps(load_entries))


class StartUpHandler(webapp2.RequestHandler):
  """URL handler class for cluster start up."""

  @decorator.oauth_required
  def get(self):
    """Starts up initial Compute Engine cluster."""
    ComputeEngineController(decorator.credentials).StartUpCluster()


class TearDownHandler(webapp2.RequestHandler):
  """URL handler class for cluster shut down."""

  @decorator.oauth_required
  def get(self):
    """Deletes Compute Engine cluster."""
    ComputeEngineController(decorator.credentials).TearDownCluster()
    LoadInfo.RemoveAllInstances()


class RegisterHandler(webapp2.RequestHandler):
  """URL handler class for IP address registration of the instance."""

  def post(self):
    """Adds the new instance to managed cluster by registering IP address."""
    # TODO(user): Secure this URL by using Cloud Endpoints.
    name = self.request.get('name')
    instance = ComputeEngineController().GetInstanceInfo(name)
    if not instance:
      return
    logging.info('Instance created: %s', str(instance))
    external_ip = instance['networkInterfaces'][0][
        'accessConfigs'][0]['natIP']
    gridstr = LoadInfo.RegisterInstanceIpAddress(name, external_ip)
    gridxy = gridstr.split(",")
    gridx = gridxy[0]
    gridy = gridxy[1]
    """Returns script to set up game server."""
    
    template = jinja_environment.get_template('setup-and-start-game.sh')
    self.response.out.write(template.render({
        'apphostname': app_identity.get_default_version_hostname(),
        'ip_address': self.request.remote_addr,
        'gridx': gridx,
        'gridy': gridy,
        'name': name
        }))

class ShutdownHandler(webapp2.RequestHandler):
  """URL handler class for deleting the instance."""

  def post(self):
    """Delete instance to managed cluster by registering IP address."""
    # TODO(user): Secure this URL by using Cloud Endpoints.
    name = self.request.get('name')
    ComputeEngineController()._DeleteInstance(name)
    self.response.out.write("Shutting down instance...");

class LoadMonitorHandler(webapp2.RequestHandler):
  def post(self):
    # TODO(user): Secure this URL by using Cloud Endpoints.
    name = self.request.get('name')
    grid = self.request.get('grid')
    
    loadresp = LoadInfo.requestLoadInfo(name, grid)
    if loadresp[LoadInfo.STATUS] == LoadInfo.STATUS_NONE:
      logging.info('STATUS_NONE so starting server for grid:'+str(grid))
      ComputeEngineController().IncreaseEngine(grid)
    if loadresp[LoadInfo.STATUS] == LoadInfo.STATUS_LOADING:
      newresp = ComputeEngineController().checkResponse(loadresp[LoadInfo.LAST_RESP])
      logging.info('Loading latest resp:'+str(newresp))
      if newresp.has_key("error"):
        logging.warn('Error loading server:'+str(newresp['error']))
        logging.warn('Removing from instances:'+str(loadresp['name']))
        LoadInfo.RemoveInstance(loadresp['name'])
      else:
        logging.info('No errors, still loading...')
    self.response.out.write(json.dumps(loadresp))


class LoadCheckerHandler(webapp2.RequestHandler):
  """URL handler class to perform cron task."""

  UPPER_THRESHOLD = 80
  LOWER_THRESHOLD = 40
  MIN_CLUSTER_SIZE = 5

  def get(self):
    """Checks average load level and adjusts cluster size if necessary.

    If average load level of instances is more than upper threshold, increase
    the number of instances by 20% of original size.  If average load level is
    less than lower threshold and the current cluster size is larger than
    minimum size, decrease the number of instances by 10%.  Since shortage
    of server is more harmful than excessive instances, we increase more
    rapidly than we decrease.

    However, shutting down the instance is more complicated than adding
    instances depending on game servers.  If client is not capable to auto-
    reconnect, the game server must be drained before shutting down the
    instance.  In this exsample, decrement of the instance is not implemented.
    """
    '''
    cluster_size, average_load = LoadInfo.GetAverageLoad()
    if cluster_size:
      if average_load > self.UPPER_THRESHOLD:
        ComputeEngineController().IncreaseEngine(cluster_size / 5 + 1)
      elif (average_load < self.LOWER_THRESHOLD and
            cluster_size > self.MIN_CLUSTER_SIZE):
        ComputeEngineController().DecreaseEngine(cluster_size / 10 + 1)
    '''
    pass



app = webapp2.WSGIApplication(
    [
        ('/getip.json', FrontendHandler),
        ('/stats', AdminUiHandler),
        ('/stats.json', StatsJsonHandler),
        ('/stats-user.json', StatsUserJsonHandler),
        ('/startup', StartUpHandler),
        ('/teardown', TearDownHandler),
        ('/register', RegisterHandler),
        ('/shutdown', ShutdownHandler),
        ('/load', LoadMonitorHandler),
        
        ('/check-load', LoadCheckerHandler),
        (decorator.callback_path, decorator.callback_handler()),
    ],
    debug=True)

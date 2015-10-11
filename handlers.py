import logging
import os

import jinja2
import uuid
import datetime
import json
from oauth2client.appengine import OAuth2Decorator
from oauth2client.client import AccessTokenRefreshError
from google.appengine.api import users
from google.appengine.ext import webapp

from compute_engine_controller import ComputeEngineController
from load_info import LoadInfo

from google.appengine.ext import db
from google.appengine.api import app_identity


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader('worker'))
    
jinja_environment_html = jinja2.Environment(
    loader=jinja2.FileSystemLoader('static_files'))


decorator = OAuth2Decorator(
    client_id = '996450208987-9259qcm3a6qh8ch15nsf6tpb0jrk2knu.apps.googleusercontent.com',
    client_secret = 'DPcR1rc9oZwBBuf6fzgj231a',
    scope=ComputeEngineController.SCOPE)

class IpAddressRequestLog(db.Model):
  """Datastore schema for game server IP address retrieval log."""
  client_ip = db.StringProperty()
  server_ip = db.StringProperty()
  timestamp = db.DateTimeProperty(auto_now=True)
  
class LoginToken(db.Model):
  # Use token as key_name
  expiration = db.DateTimeProperty()
  user_id = db.StringProperty()
  
class Entity(db.Model):
  user_id = db.StringProperty()
  gridkey = db.StringProperty()
  __type = db.StringProperty()

class GamePageHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    
    if user:
      template = jinja_environment_html.get_template('game.html')
      resp = template.render({"nickname": user.nickname(), "logouturl":users.create_logout_url('/')})
    else:
      resp = ('<html><body><a href="%s">Sign in or register</a>.</body></html>' % users.create_login_url('/'))
    
    self.response.out.write(resp)

class FrontendHandler(webapp.RequestHandler):
  """URL handler class for IP address request."""

  def get(self):
    user = users.get_current_user()
    # TODO: Check to make sure game account is up to date/paid for/whatever.
    
    # Determine what server to transfer player to
    servertoload = ""
    q = Entity.all()
    q.filter("user_id =", user.user_id())
    q.filter("__type =", "Player")
    userplayers = []
    for userplayer in q.run(limit=5):
      userplayers.append(userplayer)
    if len(userplayers) > 1:
      logging.error("UserID has more than one player")
      return
    elif len(userplayers) == 0:
      logging.info("No current players, attaching to root")
      servertoload = "0,0"
    else:
      servertoload = userplayers[0].gridkey
      
    logging.info("Loading server "+servertoload+" for "+user.nickname())
    
    info = LoadInfo.GetServerLoadInfo(servertoload)
    if info:
      if info[LoadInfo.STATUS] == LoadInfo.STATUS_UP:
        ip = info[LoadInfo.IP_ADDRESS]
        port = info[LoadInfo.PORT]
        
        # Generate login token
        token_key = uuid.uuid4().hex;
        expiration_time = datetime.datetime.now()+datetime.timedelta(seconds = 20);
        LoginToken(key_name=token_key, expiration=expiration_time, user_id=user.user_id()).put();
        
        # Send IP and token info
        self.response.out.write(json.dumps({'status':'up', 'ipaddress': ip, 'port': port, 'token': token_key}))
        IpAddressRequestLog(client_ip=self.request.remote_addr,
                            server_ip=ip).put()
      else:
        self.response.out.write(json.dumps({'status':'loading'}))
    else:
      ComputeEngineController().AddServer(servertoload)
      self.response.out.write(json.dumps({'status':'loading'}))


class AdminUiHandler(webapp.RequestHandler):
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
'''
class StatsJsonHandler(webapp.RequestHandler):
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


class StatsUserJsonHandler(webapp.RequestHandler):
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
'''

class StartUpHandler(webapp.RequestHandler):
  """URL handler class for cluster start up."""

  @decorator.oauth_required
  def get(self):
    """Starts up initial Compute Engine cluster."""
    instances = LoadInfo.GetAllInstances()
    if instances:
      raise SystemError("Instances already loaded, teardown first.");
      
    ComputeEngineController(decorator.credentials).StartUpCluster()


class TearDownHandler(webapp.RequestHandler):
  """URL handler class for cluster shut down."""

  @decorator.oauth_required
  def get(self):
    """Deletes Compute Engine cluster."""
    ComputeEngineController(decorator.credentials).TearDownCluster()
    LoadInfo.RemoveAllInstancesAndServers()


class RegisterInstanceHandler(webapp.RequestHandler):
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
    LoadInfo.RegisterInstanceIpAddress(name, external_ip)
    """Returns script to set up overarching server manager."""
    
    template = jinja_environment.get_template('setup-and-start-game.sh')
    self.response.out.write(template.render({
        'apphostname': app_identity.get_default_version_hostname(),
        'ip_address': self.request.remote_addr,
        'name': name
        }))
        
class RegisterServerHandler(webapp.RequestHandler):
  def post(self):
    """ Adds the new server to server list by registering IP/port """
    # TODO(user): Secure this URL by using Cloud Endpoints
    name = self.request.get('instancename')
    grid = self.request.get('grid')
    port = self.request.get('port')
    instance = ComputeEngineController().GetInstanceInfo(name)
    if not instance:
      logging.error("Instance name doesn't match existing instance: %s", name)
      return
    logging.info('Instance created: %s', str(instance))
    external_ip = instance['networkInterfaces'][0][
        'accessConfigs'][0]['natIP']
  
    LoadInfo.RegisterServerAddress(grid, external_ip, port)
    resp = {'external_ip':external_ip, 'success':1}
    self.response.out.write(json.dumps(resp))

class ShutdownHandler(webapp.RequestHandler):
  """URL handler class for deleting the instance."""

  def post(self):
    """Delete instance to managed cluster by registering IP address."""
    # TODO(user): Secure this URL by using Cloud Endpoints.
    name = self.request.get('name')
    ComputeEngineController().DeleteInstance(name)
    self.response.out.write(json.dumps({'success':1}));
    
class ShutdownServerHandler(webapp.RequestHandler):
  
  def post(self):
    # TODO(user): Secure this URL by using Cloud Endpoints.
    grid = self.request.get('grid')
    ComputeEngineController().RemoveServer(grid)
    self.response.out.write(json.dumps({'success':1}))

class RequireServerHandler(webapp.RequestHandler):
  """ Respond with information to connect to requested server or notify of loading status. 
  Bring server up if required. """
  
  def post(self):
    # TODO(user): Secure this URL by using Cloud Endpoints.
    grid = self.request.get('grid')
    logging.info('Received server require for grid:' + grid)
    
    loadresp = LoadInfo.GetServerLoadInfo(grid)
    if not loadresp:
      logging.info('No server so starting server for grid:'+str(grid))
      ComputeEngineController().AddServer(grid)
      loadresp = {LoadInfo.STATUS:LoadInfo.STATUS_LOADING}
    self.response.out.write(json.dumps(loadresp))
    
class InstanceUpdateHandler(webapp.RequestHandler):
  """ Accept updates from instance server manager """
  def post(self):
    # TODO: Secure this URL by using Cloud Endpoints.
    name = self.request.get('name')
    
    # TODO: Figure out credentials issues with below, likely due to ComputeEngineController credentials expiring
    #instance = ComputeEngineController().GetInstanceInfo(name)
    #if not instance:
    #  return
    
    load = int(self.request.get('load'))
    logging.info('Instance update received: ' + str(name) + ' with load: ' + str(load))
    loadresp = LoadInfo.UpdateInstanceLoadInfo(name, load)
    
    self.response.out.write(json.dumps({"loadresp":loadresp}))

class ServerUpdateHandler(webapp.RequestHandler):
  """ Accept updates from servers """
  def post(self):
    # TODO: Secure this URL by using Cloud Endpoints.
    grid = self.request.get('grid')
    num = int(self.request.get('numPlayers'))
    
    logging.info('Server update received: ' + str(grid) + ' with numPlayers: ' + str(num))
    loadresp = LoadInfo.UpdateServerNumPlayers(grid, num)
    
    self.response.out.write(json.dumps({"loadresp":loadresp}))

class HeartbeatHandler(webapp.RequestHandler):
  """URL handler class to perform cron task."""

  def get(self):
    # TODO(user): Secure this URL by using Cloud Endpoints.
    # TODO: Rebalance load
    # TODO: Make sure instances haven't crashed/stalled starting up: ComputeEngineController().checkResponse
    # TODO: Clear old LoginTokens (1 day?)
    logging.info("heartbeat")
    '''
    Possibly useful code:
    if loadresp[LoadInfo.STATUS] == LoadInfo.STATUS_LOADING:
      newresp = ComputeEngineController().checkResponse(loadresp[LoadInfo.LAST_RESP])
      logging.info('Loading latest resp:'+str(newresp))
      if newresp.has_key("error"):
        logging.warn('Error loading server:'+str(newresp['error']))
        logging.warn('Removing from instances:'+str(loadresp['name']))
        LoadInfo.RemoveInstance(loadresp['name'])
      else:
        logging.info('No errors, still loading...')
    '''
    pass



app = webapp.WSGIApplication(
    [
        ('/game', GamePageHandler),
        ('/getip.json', FrontendHandler),
        ('/stats', AdminUiHandler),
        #('/stats.json', StatsJsonHandler),
        #('/stats-user.json', StatsUserJsonHandler),
        ('/startup', StartUpHandler),
        ('/teardown', TearDownHandler),
        ('/register', RegisterInstanceHandler),
        ('/register-server', RegisterServerHandler),
        ('/shutdown', ShutdownHandler),
        ('/shutdown-server', ShutdownServerHandler),
        ('/require-server', RequireServerHandler),
        ('/update', InstanceUpdateHandler),
        ('/update-server', ServerUpdateHandler),
        
        ('/heartbeat', HeartbeatHandler),
        (decorator.callback_path, decorator.callback_handler()),
    ],
    debug=True)

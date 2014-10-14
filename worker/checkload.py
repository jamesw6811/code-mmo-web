#!/usr/bin/python


"""A program to check load level and report to Load Balancer.

Periodically checks load level and report the result to AppEngine.
The file is passed to Compute Engine instances as a start up script.
At that time, template variables are filled with real values.
"""




import os
import socket
import subprocess
import time
import urllib


class CpuUsageFetcher(object):

  NUM_PLAYERS_FILE = 'num_players'
  REGISTER_URL = 'http://{{ hostname }}/register'

  def __init__(self):
    self.hostname = socket.gethostname()
    self.prev_idle = 0
    self.prev_total = 0

  def Register(self):
    response = urllib.urlopen(self.REGISTER_URL,
                   data=urllib.urlencode({'name': self.hostname}))
    local_script_file = 'startup-and-start.sh'
    f = open(local_script_file, 'w')
    f.write(response.read())
    f.close()
    os.chmod(local_script_file, 0700)
    subprocess.call('./' + local_script_file)

'''
  def Check(self):
    """Checks CPU usage and reports to AppEngine load balancer."""
    # 8 Players are the max.
    load_level = 0;
    print("Updating "+ self.UPDATE_URL)

    # Send POST request to /load.
    urllib.urlopen(self.UPDATE_URL,
                   urllib.urlencode({'name': self.hostname,
                                     'load': load_level}))
'''

def main():
  print("Starting checkload.py. Set up game...")
  cpu_fetcher = CpuUsageFetcher()
  cpu_fetcher.Register()


if __name__ == '__main__':
  main()

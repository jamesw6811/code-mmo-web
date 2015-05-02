#!/usr/bin/python


"""A program to register the instance, download and execute the server script,
and shutdown the instance when finished. """




import os
import socket
import subprocess
import time
import urllib


class InstanceRunner(object):
  
  REGISTER_URL = 'http://{{ hostname }}/register'
  SHUTDOWN_URL = 'http://{{ hostname }}/shutdown'

  def __init__(self):
    self.hostname = socket.gethostname()

  def RegisterAndRun(self):
    # Register
    response = urllib.urlopen(self.REGISTER_URL,
                   data=urllib.urlencode({'name': self.hostname}))
    local_script_file = 'startup-and-start.sh'
    f = open(local_script_file, 'w')
    f.write(response.read())
    f.close()
    os.chmod(local_script_file, 0o700)
    
    # Run (blocking)
    subprocess.call('./' + local_script_file)
    
    # Shutdown
    print "Shutting down..."
    response = urllib.urlopen(self.SHUTDOWN_URL,
                   data=urllib.urlencode({'name': self.hostname}))
    print response

def main():
  print("Starting checkload.py. Getting hostname...")
  runner = InstanceRunner()
  print("Running startup script...")
  runner.RegisterAndRun()


if __name__ == '__main__':
  main()

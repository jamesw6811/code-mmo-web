import os
import socket
import time
import urllib

urllib.urlopen('http://subtle-palisade-726.appspot.com/register',
        data=urllib.urlencode({'name':socket.gethostname()}))
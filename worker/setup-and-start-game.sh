#!/bin/bash
CODEMMO_HOME=code-mmo
# Set up AppEngine SDK and development server.
#tar zxf google_appengine_*.tar.gz
# Set up node.js
#tar zxf node-v0.*-linux-x64.tar.gz
#ln -s node-v0.*-linux-x64 node_js
#perl -pi -e 's/MATCHER_HOST = "localhost"/MATCHER_HOST = "{{ ip_address }}"/' \
#    gritsgame/src/games-server/main.js
# Start game.
sudo apt-get update
sudo apt-get install git -y
sudo git clone https://github.com/jamesw6811/code-mmo.git
sudo apt-get install nodejs -y
sudo update-alternatives --install /usr/bin/node nodejs /usr/bin/nodejs 100
curl -L https://www.npmjs.org/install.sh | sudo sh
sudo npm install socket.io express socket.io-client request googleapis@0.4.5
node $CODEMMO_HOME/gameserver.js {{ name }} {{ gridx }} {{ gridy }} {{ apphostname }} &

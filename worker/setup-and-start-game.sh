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
sudo echo "-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEArXb3yIeL1Qdq59QYDdejnN3yrKN9t9wDPhVit7mU0haIxPrs
uu1gMoxW70WersPBDaHUk0VmSRxwpORvDUKeg+TxxphC5I2OLbNpupGZq5rRhr+o
1qknhRUW+NqKZQT7UbK8i/ZPoy8oagSmWKHB93t7gQOVs3KsbGc7D8DvcM7JbWmH
GMvYv94hCwLQHSJQwdi3jdDDcpSO5IWgbiXYZeGbPUP+14KCYn9DMxm6WOZo25IV
o+CvcpCywz6s3cN+2mdaJrYVXVKPwumhr4nY2lhLqdWcjSiDx0M0cbd5k99V9zCP
QtdzVAaFAyBVx9rsL+hYVVh/mVZpWC6ex4DY3wIDAQABAoIBADcgxAa67Tm6rcMX
qL1dduX3s5QiMWYpSe6FJWZ2WFGcT8Mqa+nMXvIxn79TROcN12DZuZFEUQmTPElr
P8/bCD2qmRwgb8HrKvBjQIrGkyvye/xzFNmD0Md+uFpGOg1409ZXE4z3rr+R0SpA
aA1q+xYH7GxIE1+AZkPdWuvayT30NCP6tkvmW+ac6lhlnmRNtFdi5t5QPyrRpCa+
2vYIjQ+OnUfqDZBWaZTQW45iHALclLjsolRKbrtl6e6T7+x98KsLu2cv/g3JJvGt
GQu2kx0Lpby7o61lVf6wWy+oczJO0VCWYV8g2gihJOa59Nq6EG4Hdxg9ZARrg6gf
CEZ9NMECgYEA1Rxv3M3im6wjusSm/Pw0xpf4oUUBTmW1kTjLK0DNYCykfJAyfhrH
NKbzxJMw15S1s6OpCcMfh782G95/2Bzi43ONxo0NIgFMqM4U2oLVmYlupnsZSgww
HLnedQ6I+QQiiQvPSZe+lfoDFypcyryruXZ+vh2yHRrHFcP8g4+WbnkCgYEA0F/v
dc1JmobpJKxTlHglCeE4KYrAP0aUkYEEO5gvrJUhoGPrbmsq+2Q0a2qxcqi/yC1r
7oPsIw5/P/bp0b/F2OUAVlq8mehADg5+m7QCe4wfP+YaRVChC2jC+RtCIgiCmB++
dtB76sFeEdyDrvl/l7UJxE5PELYfIceWvcl5TBcCgYEApeEQoUoQjSOcXBAd+uVF
Hx/Dg6P2tFMu1O7kFbLHKYkWL27+HnIxhKY/ME9xwRwbosxNEzAyJrOLJn41/L3f
TTPwsw+vnTxtsydVzA/yuyPiYOuIb7605Gc45Nx/eXTifNIYcywOSSblqO5sc9IP
yLiXRtxOe6EQPbzjnHPzn+ECgYBiAGzYI8f1RHRMijv4/RS2c9V9PEO0vtZLJLm/
6ZCqg61ACR6GXSLm/zbkOlbgzVr9o9c6Y5Ng3YWdqNxJiP9dRj8FXkGLxT6zHcAQ
LPZp8voTjH5YkVZczlW84UQWS5hYQb3LlbxiKbW7gtHwLmoDCONiD06CVpWHxp4v
/pzs2wKBgQC/UfBTu8T9aEi//+SGNu1SrtW1vStzGXub3t27/Zw7tEOtQWlzpKYS
ZUOYJaqTju5cLjitHIcY7Dn2KTB3DKYM+reMlNcKD7JGoDgh55mU8t4Wx9mqkfDg
ArSXpfm9zfNTN/Kx251uTMNL1elBpMwjr4RuJd97cG2Rs9Hvl5R9Ig==
-----END RSA PRIVATE KEY-----
" >> id_rsa
sudo bash
chmod 600 id_rsa
ssh-agent bash -c 'ssh-add id_rsa; git clone git@github.com:jamesw6811/code-mmo.git'
apt-get install nodejs -y
update-alternatives --install /usr/bin/node nodejs /usr/bin/nodejs 100
curl -L https://www.npmjs.org/install.sh | sh
npm install socket.io express socket.io-client request googleapis@0.4.5
node $CODEMMO_HOME/gameserver.js {{ name }} {{ gridx }} {{ gridy }} {{ apphostname }} &

var logintoken,
  socket, // Main socket connection
  ondecksockets,
  localPlayer; // Sockets of servers on-deck for quick movement between them


function unityMessage(method, data){
  SendMessage('NetworkController', method, JSON.stringify(data));
}

function connectToServer()
{
  unityMessage('jsRequestingServer', "");
  $.getJSON('/getip.json', function(json) {
    if (json['ipaddress']) {
      var address = json['ipaddress'];
      var port = json['port'];
      logintoken = json['token'];
      init(address, port);
    }
    else {
      console.log("Server down. Trying to reconnect...");
      setTimeout(function() {
        connectToServer();
      }, 5000);
    }
  });
}

function init(address, port){
      // Initialise socket connection
    var url = makeServerConnectionURL(address, port);
    socket = io.connect(url, {
      forceNew: true
    });
    console.log("Initializing connection with " + url);
    ondecksockets = {};
  
  
    // Start listening for network events
    setSocketHandlers();
    
    unityMessage('jsConnectingTo', ""+address+":"+port);
}

function setSocketHandlers () {
  // Socket connection successful
  socket.on("connect", onSocketConnected);

  // Socket disconnection
  socket.on("disconnect", onSocketDisconnect);

  // New player message received
  socket.on("new entity", function(data){
    if (localPlayer && (data.id == localPlayer.id)) return;
    unityMessage('jsNewEntity', data);
  });

  // Player move message received
  socket.on("update entity", function(data){
    if (localPlayer && (data.id == localPlayer.id)) return;
    unityMessage('jsUpdateEntity', data);
  });

  // Update local player message received
  socket.on("update player", function(data){
    unityMessage('jsUpdatePlayer', data);
    localPlayer = {id: data.id}; // Update localPlayer id
  });

  // Player removed message received
  socket.on("remove entity", function(data){unityMessage('jsRemoveEntity', data)});

  // Transfer servers message received
  socket.on("transfer server", onTransferServer);

  // Update on deck server to speed up transfers
  socket.on("update ondeck", onUpdateOnDeckServers);
}

function makeServerConnectionURL(address, port) {
  var portnum = Number(port) + 8000;
  return 'http://' + address + ':' + portnum + '/main';
}

function onUpdateOnDeckServers(data) {
  var servers = data.servers;
  var newondeck = {};
  // Remove repeated ondeck servers from ondecksockets and transfer to newondeck, connect to new ondeck servers
  for (var i = 0; i < servers.length; i++) {
    var url = makeServerConnectionURL(servers[i].address, servers[i].port);
    if (url in ondecksockets) {
      newondeck[url] = ondecksockets[url];
      delete ondecksockets[url];
    }
    else {
      newondeck[url] = io.connect(url, {
        forceNew: true
      });
    }
  }
  for (var decksocket in ondecksockets) { // Disconnect from non-needed sockets
    if(ondecksockets[decksocket]!=socket)ondecksockets[decksocket].disconnect();
  }
  ondecksockets = newondeck;
}

function onTransferServer(data) {
  var oldsocket = socket;
  oldsocket.removeAllListeners(); // Remove listeners and disconnect from old server
  oldsocket.disconnect();

  // Initialise new socket connection
  var url = makeServerConnectionURL(data.address, data.port);
  if (url in ondecksockets) {
    socket = ondecksockets[url];
    setSocketHandlers();
    onSocketConnected();
    console.log("Using on-deck for " + url);
  }
  else {
    socket = io.connect(url, {
      forceNew: true
    });
    setSocketHandlers();
    console.log("Initializing connection with " + url);
  }
}


// Socket connected
function onSocketConnected() {
  if (localPlayer) {
    console.log("Switched to new socket server, sending id:" + localPlayer.id);
    socket.emit("new player", {
      id: localPlayer.id
    });
    unityMessage('jsConnected', "");
  } else {
    var newPlayerReq = {
      id: null,
      token: logintoken
    };
    console.log("Connected to first socket server, sending new player req:");
    console.log(newPlayerReq);
    socket.emit("new player", newPlayerReq);
    unityMessage('jsConnected', "");
  }
}

function onSocketDisconnect() {
  console.log("Disconnected from socket server");
  unityMessage('jsDisconnected', "");
}






// Functions callable by Unity ----------

function unityStart( arg )
{
    console.log(arg);
    console.log("Unity inited. Connecting to server...");
    connectToServer();
}

function unityPrimary(data){
  /*
  socket.emit("player primary action", {
    id: ent.id,
    x: positionInWorld.x,
    y: positionInWorld.y,
    actionid: selectedAction
  });
  */
  socket.emit("player primary action", JSON.parse(data));
  console.log("player primary action");
  console.log(JSON.parse(data));
}

function unityMovePlayer(data){
  /*
    socket.emit("move player", {
      x: localPlayer.x,
      y: localPlayer.y,
      dir: localPlayer.dir
    });
  */
  
  socket.emit("move player", JSON.parse(data));
}

    

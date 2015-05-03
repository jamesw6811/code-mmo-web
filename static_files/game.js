/**
 * @fileoverview JavaScript that starts game.
 */


$(document).ready(function(){
   play();
});

/**
 * An Object representing load status of single instance.  The information is
 * generated and retrned by server in JSON format.
 *
 * @typedef {{
 *   host: string,
 *   ipaddress: string,
 *   status: string,
 *   load: number,
 *   force_set: boolean
 * }}
 */
var JsonSingleInstanceStat;



/**
 * Redirects the browser to game server to start game.
 */

var playreqsuccess = 0
function play() {
  setTimeout(function(){if(!playreqsuccess)alert("Failure requesting play server.")}, 5000);
  $.getJSON('/getip.json', function(json) {
    playreqsuccess = 1;
    if (json['ipaddress']) {
      var address = json['ipaddress'];
      var port = json['port'];
      logintoken = json['token'];
      init(address, port);
    } else {
      console.log("Server down. Trying to reconnect...");
      setTimeout(function(){play();}, 5000);
    }
  });
}


/**************************************************
** GAME VARIABLES
**************************************************/
var stage, // Main container
  renderer, // PIXI renderer
  keys,     // Keyboard input
  localPlayer,  // Local player
  entities,  // Remote players
  socket, // Main socket connection
  sprites, // Lookup of sprites by id
  textures, // Texture lookup
  logintoken,
  WIDTH = 800,
  HEIGHT = 600,
  FORGET_DISTANCE = 2000; 


/**************************************************
** GAME INITIALISATION
**************************************************/
function init(address, port) {
  // Declare the PIXI renderer and stage
	renderer = PIXI.autoDetectRenderer(WIDTH, HEIGHT, {backgroundColor : 0x1099bb});
	document.body.appendChild(renderer.view);
	stage = new PIXI.Container();
	
	loadTextures();

  // Initialise keyboard controls
  keys = new Keys();

  // Initialise array
  entities = [];
  sprites = {};
  
  
  // Initialise socket connection
  var url = makeServerConnectionURL(address, port);
  socket = io.connect(url, { forceNew: true });
  console.log("Initializing connection with "+url);


  // Start listening for events
  setEventHandlers();
  setSocketHandlers();
  
  animate();
  distanceGarbageCollect();
};

function loadTextures() {
  textures = {};
  // create a texture from an image path
  textures[1] = PIXI.Texture.fromImage('img/fighter.png');
  textures[3] = PIXI.Texture.fromImage('img/fighter.png');
  textures[10000] = PIXI.Texture.fromImage('img/grass.png');
  textures[10001] = PIXI.Texture.fromImage('img/dirt.png');
}


/**************************************************
** GAME EVENT HANDLERS
**************************************************/
var setEventHandlers = function() {
  // Keyboard
  window.addEventListener("keydown", onKeydown, false);
  window.addEventListener("keyup", onKeyup, false);

  // Window resize
  window.addEventListener("resize", onResize, false);
  
};

var setSocketHandlers = function() {
  // Socket connection successful
  socket.on("connect", onSocketConnected);

  // Socket disconnection
  socket.on("disconnect", onSocketDisconnect);

  // New player message received
  socket.on("new entity", onNewEntity);

  // Player move message received
  socket.on("move entity", onMoveEntity);
  
  // Update local player message received
  socket.on("update player", onUpdatePlayer);

  // Player removed message received
  socket.on("remove entity", onRemoveEntity);
  
  /*
  // Add viewserver message received
  socket.on("new viewserver", onNewViewServer);
  */
  
  // Transfer servers message received
  socket.on("transfer server", onTransferServer);
}

function makeServerConnectionURL(address, port){
  var portnum = Number(port) + 8000;
  return 'http://' + address + ':' + portnum + '/main';
}

function onTransferServer(data){
  /*
  var i = 0;
  for(i = 0; i < viewsockets.length; i++){
	  viewsockets[i].disconnect();
  }
  viewsockets = [];
  */
  
  socket.removeAllListeners();
  socket.disconnect();
  
  // Initialise socket connection
  var url = makeServerConnectionURL(data.address, data.port);
  socket = io.connect(url, { forceNew: true });
  setSocketHandlers();
  console.log("Initializing connection with "+url);
}

/*
function onNewViewServer(data) {
	console.log("New view server:"+data.address);
	var viewsocket = io.connect('http://' + data.address + ':8000/view', { forceNew: true });
	
	// Socket connection successful
	viewsocket.on("connect", function(){
		console.log("Connected to view server:"+data.address);
	});

	// Socket disconnection
	viewsocket.on("disconnect", function(){
		console.log("Disconnected from view server:"+data.address);
	});
	
	// New player message received
	viewsocket.on("new entity", onNewEntity);

	// Player move message received
	viewsocket.on("move entity", onMoveEntity);

	// Player removed message received
	viewsocket.on("remove entity", onRemoveEntity);
	
    viewsockets.push(viewsocket);
}
*/

// Keyboard key down
function onKeydown(e) {
  if (localPlayer) {
    keys.onKeyDown(e);
  };
};

// Keyboard key up
function onKeyup(e) {
  if (localPlayer) {
    keys.onKeyUp(e);
  };
};

// Browser window resize
function onResize(e) {
};

// Socket connected
function onSocketConnected() {
  if (localPlayer){
    console.log("Switched to new socket server, sending id:"+localPlayer.id);
    socket.emit("new player", {id : localPlayer.id});
  } else {
    var newPlayerReq = {id : null, token : logintoken};
    console.log("Connected to first socket server, sending new player req:");
    console.log(newPlayerReq);
    socket.emit("new player", newPlayerReq);
  }
};

function onSocketDisconnect() {
  console.log("Disconnected from socket server");
  entities = []
};

function onNewEntity(data) {
  //console.log("New entity: "+data.id);
	onMoveEntity(data);  // always use onMove -- onNew will be called if it doesn't exist
};

function onMoveEntity(data) {
  if (localPlayer && (data.id == localPlayer.id))return;
  
  var moveEntity = entityById(data.id);

  if (!moveEntity) {
	  addEntity(data);
  } else {
    updateEntity(moveEntity, data);
  }

  // Update Entity position
};

function onUpdatePlayer(player) {
  console.log(player);
  if (!localPlayer){
    localPlayer = new Player();
	  localPlayer.id = player.id;
	  localPlayer.updateFromEmit(player);
	  entities.push(localPlayer);
	  
  	// Add to graphics
  	var texture = getGraphicTexture(localPlayer.graphic);
    var sprite = new PIXI.Sprite(texture);
    sprite.anchor.x = 0.5;
    sprite.anchor.y = 0.5;
    sprite.height = 50;
    sprite.width = 50;
    sprites[localPlayer.id] = sprite;
    stage.addChild(sprite);
    setSpriteLocation(sprite, localPlayer);
  } else {
    updateEntity(localPlayer, player);
  }
  console.log("Update:");
	console.log(player);
}

function updateEntity(moveEntity, data) {
	  moveEntity.updateFromEmit(data);
	  
	  var sprite = sprites[moveEntity.id];
	  setSpriteTexture(sprite, moveEntity);
	  setSpriteLocation(sprite, moveEntity);
}

function addEntity(data) {
  var ent = new Entity(data.id);
	ent.updateFromEmit(data);
  entities.push(ent);
	
	// Add to graphics
	var texture = getGraphicTexture(ent.graphic);
  var sprite = new PIXI.Sprite(texture);
  sprite.height = 50;
  sprite.width = 50;
  sprite.anchor.x = 0.5;
  sprite.anchor.y = 0.5;
  sprites[ent.id] = sprite;
  stage.addChild(sprite);
  setSpriteLocation(sprite, ent);
}

function onRemoveEntity(data) {
  var removeEntity = entityById(data.id);
  // Player not found
  if (!removeEntity) {
    console.log("Entity not found: "+data.id);
    return;
  }
  // Remove player from array
  entities.splice(entities.indexOf(removeEntity), 1);
  
  // Remove from graphics
  var sprite = sprites[removeEntity.id];
  stage.removeChild(sprite);
  delete sprites[removeEntity.id];
};

function getGraphicTexture(graphic) {
	if (graphic in textures){
	  return textures[graphic];
	} else {
	  return textures[1]; // Default texture :P
	}
}

function setSpriteTexture(sprite, ent) {
  sprite.texture = getGraphicTexture(ent.graphic);
}

function setSpriteLocation(sprite, ent) {
  sprite.position.x = ent.x;
  sprite.position.y = ent.y;
  if (ent.dir) {
    sprite.rotation = ent.dir - Math.PI/2;
  } else {
    sprite.rotation = -Math.PI/2;
  }
  if (sprite.z && sprite.z == ent.layer){
    // Ignore if z is staying the same
  } else {
    sprite.z = ent.layer;
    stage.children.sort(depthCompare); // Sort children to put right things on top
  }
}

/**************************************************
** GAME UPDATE
**************************************************/
function update() {
  // Update local player and check for change
  if (localPlayer.updateKeys(keys)) {
    // Send local player data to the game server
    socket.emit("move player", {x: localPlayer.x, y: localPlayer.y, dir: localPlayer.dir});
    var playerSprite = sprites[localPlayer.id];
    setSpriteLocation(playerSprite, localPlayer);
  }
}

function distanceGarbageCollect(){
  if (localPlayer){
    var toRemove = [];
    // Check for entities out of range
    for (var i = 0; i < entities.length; i++){
      var xDis = Math.abs(entities[i].x-localPlayer.x);
      var yDis = Math.abs(entities[i].y-localPlayer.y);
      if (xDis > FORGET_DISTANCE || yDis > FORGET_DISTANCE){
        toRemove.push(entities[i]);
      }
    }
    // Remove out of range entities
    for (var i = 0; i < toRemove.length; i++){
      onRemoveEntity(toRemove[i]);
    }
  }
  setTimeout(distanceGarbageCollect, 2000);
}


/**************************************************
** GAME DRAW
**************************************************/
function animate() {
  requestAnimationFrame(animate);
  if (localPlayer){
    update(); // TODO: wrap in time variable to make movement speed constant with FPS
    
    
    stage.rotation = -localPlayer.dir+Math.PI/2;
    stage.pivot.x = localPlayer.x;
    stage.pivot.y = localPlayer.y;
    stage.x = WIDTH/2;
    stage.y = HEIGHT/2;
    
    // render the container
    renderer.render(stage);
  } else {
    // TODO: Render loading container
    renderer.render(stage);
  }
};


/**************************************************
** GAME HELPER FUNCTIONS
**************************************************/
function entityById(id) {
  var i;
  for (i = 0; i < entities.length; i++) {
    if (entities[i].id == id)
      return entities[i];
  };
  
  return false;
};

function depthCompare(a,b) {
  if (a.z < b.z)
     return -1;
  if (a.z > b.z)
    return 1;
  return 0;
}




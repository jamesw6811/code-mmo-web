/**
 * @fileoverview JavaScript that starts game.
 */


$(document).ready(function(){
  $("p").click(function(){
   play();
  });
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
      init('http://' + json['ipaddress'] + ':8000/main');
      animate();
    } else {
      alert('No Game Server Available.');
    }
  });
}


/**************************************************
** GAME VARIABLES
**************************************************/
var canvas,     // Canvas DOM element
  ctx,      // Canvas rendering context
  keys,     // Keyboard input
  localPlayer,  // Local player
  entities,  // Remote players
  socket, // Main socket connection
  viewsockets;     // Socket connections for extra views


/**************************************************
** GAME INITIALISATION
**************************************************/
function init(url) {
  // Declare the canvas and rendering context
  canvas = document.getElementById("gameCanvas");
  ctx = canvas.getContext("2d");

  // Maximise the canvas
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  // Initialise keyboard controls
  keys = new Keys();

  // Calculate a random start position for the local player
  // The minus 5 (half a player size) stops the player being
  // placed right on the egde of the screen
  var startX = Math.round(Math.random()*(canvas.width-5)),
    startY = Math.round(Math.random()*(canvas.height-5));

  // Initialise the local player
  localPlayer = new Player();
  localPlayer.id = null;

  // Initialise array
  entities = [];
  entities.push(localPlayer);
  
  viewsockets = [];
  // Initialise socket connection
  socket = io.connect(url);
  console.log("Initializing connection with "+url);


  // Start listening for events
  setEventHandlers();
  setSocketHandlers();
};


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
  
  // Add viewserver message received
  socket.on("new viewserver", onNewViewServer);
  
  // Transfer servers message received
  socket.on("transfer server", onTransferServer);
}

function onTransferServer(data){
  var i = 0;
  for(i = 0; i < viewsockets.length; i++){
	  viewsockets[i].disconnect();
  }
  viewsockets = [];
  socket.removeAllListeners();
  socket.disconnect();
  // Initialise socket connection
  socket = io.connect('http://' + data.address + ':8000/main');
  console.log("Initializing connection with "+data.address);
  setSocketHandlers();
}

function onNewViewServer(data) {
	console.log("New view server:"+data.address);
	var viewsocket = io.connect('http://' + data.address + ':8000/view');
	console.log("Initializing connection...");
	
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
  // Maximise the canvas
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
};

// Socket connected
function onSocketConnected() {
  console.log("Connected to socket server, sending id:"+localPlayer.id);
  socket.emit("new player", {id : localPlayer.id});
};

function onSocketDisconnect() {
  console.log("Disconnected from socket server");
  entities = []
};

function onNewEntity(data) {
  //console.log("New entity: "+data.id);
	addEntity(data);
};

function onMoveEntity(data) {
  var moveEntity = entityById(data.id);

  if (!moveEntity) {
    console.log("Entity not found: "+data.id);
	addEntity(data);
  } else {
	moveEntity.updateFromEmit(data);
  }

  // Update Entity position
};

function onUpdatePlayer(player) {
	localPlayer.updateFromEmit(player);
	localPlayer.id = player.id;
	console.log(player);
}

function addEntity(data) {
    var ent = new Entity(data.id);
	ent.updateFromEmit(data);
    entities.push(ent);
	entities.sort(function(enta, entb){return entb.layer-enta.layer});
}

// Remove player
function onRemoveEntity(data) {
  var removeEntity = entityById(data.id);

  // Player not found
  if (!removeEntity) {
    console.log("Entity not found: "+data.id);
    return;
  };

  // Remove player from array
  entities.splice(entities.indexOf(removeEntity), 1);
};



/**************************************************
** GAME ANIMATION LOOP
**************************************************/
function animate() {
  update();
  draw();

  // Request a new animation frame using Paul Irish's shim
  window.requestAnimFrame(animate);
};


/**************************************************
** GAME UPDATE
**************************************************/
function update() {
  // Update local player and check for change
  if (localPlayer.updateKeys(keys)) {
    // Send local player data to the game server
    socket.emit("move player", {x: localPlayer.x, y: localPlayer.y});
  };
};


/**************************************************
** GAME DRAW
**************************************************/
function draw() {

  // Wipe the canvas clean
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(-localPlayer.x+canvas.width/2, -localPlayer.y+canvas.height/2);

  var i;
  for (i = 0; i < entities.length; i++) {
    entities[i].draw(ctx);
  };
  ctx.restore();
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

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
    playreqsuccess = 1
    if (json['ipaddress']) {
      init('http://' + json['ipaddress'] + ':8000');
      animate()
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
  socket;     // Socket connection


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
  localPlayer = new Player(startX, startY);

  // Initialise socket connection
  socket = io.connect(url);
  console.log("Initializing connection with "+url);

  // Initialise remote players array
  entities = [];

  // Start listening for events
  setEventHandlers();
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

  // Socket connection successful
  socket.on("connect", onSocketConnected);

  // Socket disconnection
  socket.on("disconnect", onSocketDisconnect);

  // New player message received
  socket.on("new entity", onNewEntity);

  // Player move message received
  socket.on("move entity", onMoveEntity);

  // Player removed message received
  socket.on("remove entity", onRemoveEntity);
};

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
  console.log("Connected to socket server");

  socket.emit("new player", {x: localPlayer.x, y: localPlayer.y});
};

function onSocketDisconnect() {
  console.log("Disconnected from socket server");
  entities = []
};

function onNewEntity(data) {
  console.log("New entity: "+data.id);

  var newEntity = new Entity(data.x, data.y);
  newEntity.id = data.id;

  entities.push(newEntity);
};

function onMoveEntity(data) {
  var moveEntity = entityById(data.id);

  if (!moveEntity) {
    console.log("Entity not found: "+data.id);
    moveEntity = new Entity(data.x, data.y);
    moveEntity.id = data.id;
    entities.push(moveEntity);
  };

  // Update Entity position
  moveEntity.x = data.x;
  moveEntity.y = data.y;
};

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

  localPlayer.draw(ctx);

  var i;
  for (i = 0; i < entities.length; i++) {
    entities[i].draw(ctx);
  };
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

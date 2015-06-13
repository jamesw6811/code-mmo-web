if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    Entity = require("./Entity").Entity;    // Entity class
Player.prototype = new Entity();
Player.prototype.constructor=Player;
function Player(){
    Entity.apply(this, arguments);
	this.x = 100;
	this.y = 100;
	this.dir = 0;
    this.graphic = 1;       
    this.moveAmount = 2;
    this.turnAmount = 0.04;
	this.layer = 5;
    this.viewDistanceSquared = Math.pow(500, 2);
	
	this.clientid = null; // Reserved for setting
	this.socket = null;
}

/*
Player.prototype.toDS = function() {
	return {
		__type: {stringValue: 'Player'},
		x: {integerValue: this.x},
		y: {integerValue: this.y},
		dir: {integerValue: this.dir},
		id: {stringValue: this.id}
	};
};
Player.fromDS = function(data){
	var ent = new Player(data.id.stringValue);
	ent.x = data.x.integerValue;
	ent.y = data.y.integerValue;
	ent.dir = data.dir.integerValue;
	return ent;
}
*/	

Entity.Types.Player = Player;

if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    exports.Player = Player;
else
    window.Player = Player;

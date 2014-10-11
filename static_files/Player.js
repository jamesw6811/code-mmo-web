if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    Entity = require("./Entity").Entity;    // Entity class
Player.prototype = new Entity();
Player.prototype.constructor=Player;
function Player(){
    Entity.apply(this, arguments);
	this.x = 100;
	this.y = 100;
    this.graphic = 1;       
    this.moveAmount = 2;
	this.layer = 0;
	
	this.clientid = null; // Reserved for setting
	this.socket = null;
}

Player.prototype.updateKeys = function(keys) {
        // Previous position
        var prevX = this.x,
            prevY = this.y;

        // Up key takes priority over down
        if (keys.up) {
            this.y -= this.moveAmount;
        } else if (keys.down) {
            this.y += this.moveAmount;
        };

        // Left key takes priority over right
        if (keys.left) {
            this.x -= this.moveAmount;
        } else if (keys.right) {
            this.x += this.moveAmount;
        };

        return (prevX != this.x || prevY != this.y) ? true : false;
    };

Player.prototype.draw = function(ctx) {
		ctx.fillStyle = "#888888";
        ctx.fillRect(this.x-5, this.y-5, 10, 10);
    };
	
	
Player.prototype.toDS = function() {
	return {
		__type: {stringValue: 'Player'},
		x: {integerValue: this.x},
		y: {integerValue: this.y},
		id: {stringValue: this.id},
		moveAmount: {integerValue: this.moveAmount}
	};
};
Player.fromDS = function(data){
	var ent = new Player(data.id.stringValue);
	ent.x = data.x.integerValue;
	ent.y = data.y.integerValue;
	ent.moveAmount = data.moveAmount.integerValue;
	return ent;
}
	

Entity.Types.Player = Player;

if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    exports.Player = Player;
else
    window.Player = Player;

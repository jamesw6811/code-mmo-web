if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    Entity = require("./Entity").Entity;    // Entity class
Player.prototype = new Entity();
Player.prototype.constructor=Player;
function Player(){
    this.x = 5;
    this.y = 5;
    this.graphic = 1;       
    this.moveAmount = 2;
    this.id = Entity.nextid;
    Entity.nextid = Entity.nextid + 1;
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
        ctx.fillRect(this.x-5, this.y-5, 10, 10);
    };

if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    exports.Player = Player;
else
    window.Player = Player;

// Entity is the super class for all graphical objects passed to client.
function Entity(id) {
	if (id === undefined){
		this.id = Entity.serverid*Entity.MACHINESHIFT + Entity.nextid*Entity.IDSHIFT;
		Entity.nextid = Entity.nextid + 1;
	} else {
		this.id = id;
	}
	
    this.x = 0;
    this.y = 0;
    this.graphic = 0;
}
Entity.MACHINESHIFT = 4294967296;
Entity.IDSHIFT = 1;
Entity.nextid = 0;
Entity.GRAPHICS = {1 : '#000000', 3 : '#FF0000', 10000 : '#00FF00', 10001: '#22FF00'};

Entity.prototype.getEmit = function(){
	return {id: this.id, x: this.x, y: this.y, graphic: this.graphic};
}
Entity.prototype.distanceSquaredTo = function(ent){
    var xdis = ent.x - this.x;
    var ydis = ent.y - this.y;
    return xdis*xdis+ydis*ydis;
}
Entity.prototype.draw = function(ctx) {
	var g = Entity.GRAPHICS[this.graphic];
	if (g === undefined){
		ctx.fillStyle = "#888888";
	} else {
		ctx.fillStyle = g;
	}
    ctx.fillRect(this.x-10, this.y-10, 20, 20);
	ctx.fillStyle = "#888888";
	ctx.strokeRect(this.x-10, this.y-10, 20, 20);
};



if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    exports.Entity = Entity;
else
    window.Entity = Entity;
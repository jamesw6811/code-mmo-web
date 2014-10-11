// Entity is the super class for all graphical objects passed to client.
function Entity(id) {
	if (id === undefined){
		this.id = (Entity.serverid*Entity.MACHINESHIFT).toString(32) + ',' + (Entity.nextid*Entity.IDSHIFT).toString(32);
		Entity.nextid = Entity.nextid + 1;
	} else {
		this.id = id;
	}
	this.layer = 0;
    this.x = 0;
    this.y = 0;
    this.graphic = 0;
}
Entity.MACHINESHIFT = 4294967296;
Entity.IDSHIFT = 1;
Entity.nextid = 0;
Entity.GRAPHICS = {1 : '#000000', 3 : '#FF0000', 10000 : '#00FF00', 10001: '#22FF00'};

Entity.prototype.getEmit = function(){
	return {id: this.id, x: this.x, y: this.y, graphic: this.graphic, layer: this.layer};
}
Entity.prototype.updateFromEmit(data){
	this.x = data.x;
	this.y = data.y;
	this.graphic = data.graphic;
	this.layer = data.layer;
}
Entity.makeFromEmit(data){
	var ent = new Entity(data.id);
	ent.x = data.x;
	ent.y = data.y;
	ent.graphic = data.graphic;
	ent.layer = data.layer;
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
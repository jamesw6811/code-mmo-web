// Entity is the super class for all graphical objects passed to client.
function Entity(id) {
	if (id === undefined){
		this.id = Entity.serverid + ',' + (Entity.nextid).toString(32);
		Entity.nextid = Entity.nextid + 1;
	} else {
		this.id = id;
	}
	this.layer = 0;
    this.x = 0;
    this.y = 0;
    this.graphic = 0;
}
Entity.Types = {};
Entity.Types.Entity = Entity;
Entity.MACHINESHIFT = 4294967296;
Entity.IDSHIFT = 1;
Entity.nextid = 0;
Entity.GRAPHICS = {1 : '#00FF00', 3 : '#FF0000', 10000 : '#00FF00', 10001: '#888800'};

Entity.prototype.getEmit = function(){
	return {id: this.id, x: this.x, y: this.y, dir: this.dir, graphic: this.graphic, layer: this.layer};
}
Entity.prototype.updateFromEmit = function(data){
	this.x = data.x;
	this.y = data.y;
	this.dir = data.dir;
	this.graphic = data.graphic;
	this.layer = data.layer;
}
Entity.makeFromEmit = function(data){
	var ent = new Entity(data.id);
	ent.x = data.x;
	ent.y = data.y;
	ent.dir = data.dir;
	ent.graphic = data.graphic;
	ent.layer = data.layer;
	return ent;
}
Entity.prototype.distanceSquaredTo = function(ent){
    var xdis = ent.x - this.x;
    var ydis = ent.y - this.y;
    return xdis*xdis+ydis*ydis;
}
Entity.prototype.draw = function(ctx) {
	ctx.save();
	
	// Transform and rotate to entity
  	ctx.translate(this.x, this.y);
  	if (this.dir){
		ctx.rotate(this.dir*Math.PI/180);
	}
	
  	// Draw entity
	var g = Entity.GRAPHICS[this.graphic];
	if (g === undefined){
		ctx.fillStyle = "#888888";
	} else {
		ctx.fillStyle = g;
	}
    ctx.fillRect(-10, -10, 20, 20);
	ctx.fillStyle = "#888888";
	ctx.strokeRect(-10, -10, 20, 20);
	
	ctx.restore();
};


Entity.prototype.toDS = function() {
	return {
		__type: {stringValue: 'Entity'},
		x: {integerValue: this.x},
		y: {integerValue: this.y},
		id: {stringValue: this.id},
		layer: {integerValue: this.layer},
		graphic: {integerValue: this.graphic}
	};
};
Entity.fromDS = function(data){
	var ent = new Entity(data.id.stringValue);
	ent.x = data.x.integerValue;
	ent.y = data.y.integerValue;
	ent.layer = data.layer.integerValue;
	ent.graphic = data.graphic.integerValue;
	return ent;
}


if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    exports.Entity = Entity;
else
    window.Entity = Entity;
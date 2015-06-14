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
    this.vx = 0; // visual x-velocity per ms
    this.vy = 0; // visual y-velocity per ms
    this.dir = 0;
    this.graphic = 0;
}
Entity.Types = {};
Entity.Types.Entity = Entity;
Entity.MACHINESHIFT = 4294967296;
Entity.IDSHIFT = 1;
Entity.nextid = 0;

Entity.prototype.getEmit = function(){
	return {id: this.id, x: this.x, y: this.y, dir: this.dir, graphic: this.graphic, layer: this.layer};
}
Entity.prototype.updateFromEmit = function(data){
	this.x = data.x;
	this.y = data.y;
    this.vx = data.vx; 
    this.vy = data.vy; 
	this.dir = data.dir;
	this.graphic = data.graphic;
	this.layer = data.layer;
}
Entity.makeFromEmit = function(data){
	var ent = new Entity(data.id);
	ent.x = data.x;
	ent.y = data.y;
    ent.vx = data.vx; 
    ent.vy = data.vy; 
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


if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    exports.Entity = Entity;
else
    window.Entity = Entity;
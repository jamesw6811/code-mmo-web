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

Entity.prototype.distanceSquaredTo = function(ent){
    var xdis = ent.x - this.x;
    var ydis = ent.y - this.y;
    return xdis*xdis+ydis*ydis;
}
Entity.prototype.draw = function(ctx) {
    ctx.fillRect(this.x-10, this.y-10, 20, 20);
};

if (typeof module !== 'undefined' && typeof module.exports !== 'undefined')
    exports.Entity = Entity;
else
    window.Entity = Entity;
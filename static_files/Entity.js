function Entity(startX, startY) {
    this.x = startX,
    this.y = startY,
    this.graphic = 0;
    this.id = Entity.nextid;
    Entity.nextid = Entity.nextid + 1;
}
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

/**************************************************
** GAME KEYBOARD CLASS
**************************************************/
var Keys = function(up, left, right, down, w_key, a_key, s_key, d_key) {
	var up = up || false,
		left = left || false,
		right = right || false,
		down = down || false,
		w_key = w_key || false,
		a_key = a_key || false,
		s_key = s_key || false,
		d_key = d_key || false,
		pressed = [];
		
	var onKeyDown = function(e) {
		var that = this,
			c = e.keyCode;
		switch (c) {
			// Controls
			case 37: // Left
				that.left = true;
				pressed.push("left");
				break;
			case 38: // Up
				that.up = true;
				pressed.push("up");
				break;
			case 39: // Right
				that.right = true;
				pressed.push("right");
				break;
			case 40: // Down
				that.down = true;
				pressed.push("down");
				break;
			case 87: // W
				that.w_key = true;
				pressed.push("w_key");
        		console.log(pressed);
				break;
			case 65: // A
				that.a_key = true;
				pressed.push("a_key");
				break;
			case 83: // S
				that.s_key = true; 
				pressed.push("s_key");
				break;
			case 68: // D
				that.d_key = true;
				pressed.push("d_key");
				break;
		}
	};
	
	var onKeyUp = function(e) {
		var that = this,
			c = e.keyCode;
		switch (c) {
			case 37: // Left
				that.left = false;
				break;
			case 38: // Up
				that.up = false;
				break;
			case 39: // Right
				that.right = false;
				break;
			case 40: // Down
				that.down = false;
				break;
			case 87: // W
				that.w_key = false;
				break;
			case 65: // A
				that.a_key = false;
				break;
			case 83: // S
				that.s_key = false;
				break;
			case 68: // D
				that.d_key = false;
				break;
		}
	};
	
	var resetPressed = function(){
		this.pressed.length = 0;
	};

	return {
		up: up,
		left: left,
		right: right,
		down: down,
		w_key: w_key,
		a_key: a_key,
		s_key: s_key,
		d_key: d_key,
		pressed: pressed,
		onKeyDown: onKeyDown,
		onKeyUp: onKeyUp,
		resetPressed: resetPressed
	};
};
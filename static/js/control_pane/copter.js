/* Copter */
(function (window) {
    window.Copter = function (arParams) {
    	this.object_type = "copter";
    	this.template_parts = {
    		'placemark':'',
			'baloon':'',
			'RTL':''
		};
        this.roiSwitch = false;
        this.buildCommandSwitch = false;
    	this.home_location = arParams.home_location;
    	var self = this;
    	if (arParams){
    		self.id = arParams.id;
    		self.name = arParams.name;
    		self.base_id = arParams.base_id;
			self.route = arParams.route;
    		self.properties = arParams.properties;
    		self.Init();
    	}
    }
    window.Copter.prototype.positionUpdater = function(){
    	var self = this;
    	setInterval(function(){
    		if (self.properties.coordinates_lat != undefined && self.template_parts != undefined && self.properties.coordinates_lat != "None"){
    			self.template_parts['placemark'].geometry.setCoordinates([self.properties.coordinates_lat, self.properties.coordinates_lon]);
			}

		}, 1000);
	}
    window.Copter.prototype.Init = function(){
    	this.template_parts = window.MapObjectTemplate.Init(this);
    	this.positionUpdater();
    }
})(window);
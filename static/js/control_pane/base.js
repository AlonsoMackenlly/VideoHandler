/* Copter */
(function (window) {
    window.Base = function (arParams) {
        this.template_parts = {
            'circle':''
        };
        this.object_type = "base";
    	var self = this;
    	if (arParams){
    		self.properties = arParams;
    		self.Init();
    	}
    }
    window.Base.prototype.Init = function(){
    	window.MapObjectTemplate.Init(this);
    }
})(window);
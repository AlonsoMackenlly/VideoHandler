/* ControllPanel */
(function (window) {
    window.JCControllPane = function () {
        this.bases = app.bases;
        this.copters = app.copters;
        this.cancelling = false;
        this.is_drawing = false;
        this.Init();
    };

    window.JCControllPane.prototype.InitBases = function () {
        for (base in this.bases) {
            this.bases[base] = new window.Base(this.bases[base]);
            //console.log(this.copters[copter]);
        }
    }
    window.JCControllPane.prototype.InitCopters = function () {
        for (copter in this.copters) {
            this.copters[copter] = new window.Copter(this.copters[copter]);
        }
    }
    window.JCControllPane.prototype.Init = function () {
        this.InitBases();
        this.InitCopters();
        window.mapControl = new window.mapControl({});
        window.WebSocketMessages = new window.WebSocketMessages({});
        window.WebSocketMessages.sender();
        
        //this.mapDrawing = new window.mapDrawing({1:1});
    }
    window.JCControllPane.prototype.findCopterByID = function (copter_id) {
        var self = this;
        for (id in self.copters) {
            if (id == copter_id) {
                return self.copters[id];
            }
        }
    }
    window.JCControllPane.prototype.update_statistic = function () {

    };
    window.JCControllPane.prototype.uid = function () {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    window.JCControllPane.prototype.deleteData = function(){
        var intervalID = setInterval(function(){
            if (wsListener.connected == true){
                window.wsListener.send_message({
                    type: 'delete_data',
                    data: {}
                });
                notSended = false;
                clearInterval(intervalID);
            }
        }, 1000);
    }
    window.JCControllPane.prototype.wsListener = window.wsListener;
    window.JCControllPane.prototype.mapDrawing = window.mapDrawing;

    // JCControllPane.wsListener = window.wsListener;

})(window);


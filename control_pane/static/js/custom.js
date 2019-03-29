/* Page builder */
(function (window) {
    window.pageBuilder = { };
    window.pageBuilder.init = function () {
        $('.copter-list-item').on('click', this.checkActiveCopterListItem);
    };
    window.pageBuilder.checkActiveCopterListItem = function(event){
        var copter_id = $(this).attr('data-copter-id');
        $('.sub-menu.collapse').not("#copter_action_list_"+copter_id).css('display', 'none');
        //$('.sub-menu.collapse').not("#copter_action_list_"+copter_id).collapse('hide');
        $('.copter-list-item').not($(this)).removeClass('active');
        $('.copter_stats').not($('#copter_stats_'+copter_id)).removeClass('active');

        if ($(this).hasClass('active')){
            $(this).removeClass('active');
            $('.bottom-pane').removeClass('active');
            $('#copter_stats_'+copter_id).removeClass('active');
            $('#copter_action_list_'+copter_id).css('display', 'none');
        }
        else{
            $('#copter_action_list_'+copter_id).css('display', 'block');
            $(this).addClass('active');
            if (!$('.bottom-pane').hasClass('active')){
                $('.bottom-pane').addClass('active');
            }
            $('#copter_stats_'+copter_id).addClass('active');
        }
    };
    window.pageBuilder.init();

})(window);

/* Copter */
(function (window) {
    window.Copter = function (arParams) {
    }
})(window);

/* mapDrawing */
(function (window) {
    window.mapDrawing = function (arParams) {
    };
})(window);

/* wsListener */
(function (window) {
    var wsListener = {};
    window.wsListener = wsListener;

    var self = wsListener;
    self.connected = false;
    self.connect = function(){
    	try {
            Csocket = new WebSocket(window.WS_CONNECTION_STRING);
            wsListener.Csocket = Csocket;
            Csocket.onopen = function () {
                console.log("Соединение установлено.");
                self.connected = true;
                setInterval(function () {
                    wsListener.send_message({type: "update_statistic"}); // обновляем показатели коптера в панели
                }, 500);
            };
            Csocket.onclose = function (event) {
                if (event.wasClean) {
                    console.log('Соединение закрыто чисто');
                } else {
                    console.log('Обрыв соединения'); // например, "убит" процесс сервера
                }
                console.log('Код: ' + event.code + ' причина: ' + event.reason);
                self.connected = false;
            };
            Csocket.update_statistic = function (data) {
                $("#altitude").text(data.coordinates_alt);
                $("#speed").text(data.ground_speed);
                $("#state").text(data.status);
                $("#mode").text(data.mode);
                $("#battery_level").text(data.battery_level + " %, " + data.battery_voltage + " V");
                $("#last_heartbeat").text(data.last_heartbeat);
                $("#gps_fixed").text(data.gps_fixed);
                $("#connection").text(data.connection)
            };
            Csocket.onmessage = function (event) {
                self.isHandling = false;
                try {
                    if (event.data != "" && event.data != null && event.data != undefined) {
                        var response = JSON.parse(event.data);
                        if (response.hasOwnProperty("type")) {
                            if (response.type == "update_statistic") {
                                Csocket.update_statistic(response.data);
                            } else if (response.message == "draw routes") {

                            }
                        }
                    }
                } catch (e) {
                    console.log(response);
                    console.log(e);
                    console.log(event.data);
                }
            };

            Csocket.onerror = function (error) {
                console.log(error);
                console.log("Ошибка " + error.message);
                self.connected = false;
            };
            wsListener.send_message = function (message) {
                Csocket.send(JSON.stringify(message));
            };
        } catch (e) {
            //console.log(e)
        }
    }
    var Csocket;
    var intervalID = setInterval(function () {
        if (self.connected == false) {
        //} else {
        	self.connect();
        }
    }, 2000);


})(window);

/* ControllPanel */
(function (window) {
    window.JCControllPane = function (arParams) {
        this.copters = arParams.copters;
    };
    window.JCControllPane.prototype.update_statistic = function () {

    };
    // window.JCControllPane.wsListener = window.wsListener;
    // window.JCControllPane.mapDrawing = window.mapDrawing;
    // JCControllPane.wsListener = window.wsListener;

})(window);

$(document).ready(function () {
    ymaps.ready(init);

    function init() {
        window.Ymap = new window.ymaps.Map('map', {
            // При инициализации карты обязательно нужно указать
            // её центр и коэффициент масштабирования.
            center: [53.527197, 49.368830],
            zoom: 13,
            controls: []
        }, {
            searchControlProvider: 'yandex#search'
        });
    }

});

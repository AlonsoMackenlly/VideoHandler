/* wsListener */
(function (window) {
    var wsListener = {
        socket: '',
        connected: false,
        notSendedMessages: [], // Неотправленные сообщения копятся здесь
        notDoneMessages: [], // После отправки помещаются сюда, чтобы отследить обработку на сервере по uid, затем удаляется
    };

    wsListener.connect = function () {
        var self = this;
        try {
            self.socket = new WebSocket(window.WS_CONNECTION_STRING);
            self.socket.onopen = function () {
                console.log("Соединение установлено.");
                self.connected = true;
            };
            self.socket.onclose = function (event) {
                if (event.wasClean) {
                    //console.log('Соединение закрыто чисто');
                } else {
                    //console.log('Обрыв соединения'); // например, "убит" процесс сервера
                }
                //console.log('Код: ' + event.code + ' причина: ' + event.reason);
                self.connected = false;
                setTimeout(function () {
                    wsListener.connect();
                }, 2000);
                // setTimeout(function () {
                //     wsListener.connect();
                // }, 10000);

            };
            self.socket.onmessage = function (event) {
                WebSocketMessages.handle(event);
            };

            self.socket.onerror = function (error) {
                // console.log(error);
                // console.log("Ошибка " + error.message);
                self.connected = false;
                //self.socket.close();
                self.socket = undefined;
                // setTimeout(function () {
                //     wsListener.connect();
                // }, 1000);

            };

        } catch (e) {
            //console.log(e);
            wsListener.connect();
            self.connected = false;
            self.socket.close();
            self.socket = undefined;

        }
    };
    wsListener.send_message = function (message) {
        this.socket.send(JSON.stringify(message));
    };
    setTimeout(function(){
        wsListener.connect();
    }, 2000);
    // var intervalID = setInterval(function () {
    //     if (wsListener.connected == false) {
    //         wsListener.connect();
    //     }
    // }, 5000);
    window.wsListener = wsListener;

})(window);


// /* wsListener */
// (function (window) {
//     var wsListener = {};
//     window.wsListener = wsListener;

//     var self = wsListener;
//     self.connected = false;
//     self.connect = function(){
//         try {
//             Csocket = new WebSocket(window.WS_CONNECTION_STRING);
//             wsListener.Csocket = Csocket;
//             Csocket.onopen = function () {
//                 console.log("Соединение установлено.");
//                 self.connected = true;
//                 setInterval(function () {
//                     wsListener.send_message({type: "update_statistic"}); // обновляем показатели коптера в панели
//                 }, 500);
//             };
//             Csocket.onclose = function (event) {
//                 if (event.wasClean) {
//                     console.log('Соединение закрыто чисто');
//                 } else {
//                     console.log('Обрыв соединения'); // например, "убит" процесс сервера
//                 }
//                 console.log('Код: ' + event.code + ' причина: ' + event.reason);
//                 self.connected = false;
//             };
//             // TODO: переместить в page_builder
//             Csocket.update_statistic = function (data) {
//                 $("#altitude").text(data.coordinates_alt);
//                 $("#speed").text(data.ground_speed);
//                 $("#state").text(data.status);
//                 $("#mode").text(data.mode);
//                 $("#battery_level").text(data.battery_level + " %, " + data.battery_voltage + " V");
//                 $("#last_heartbeat").text(data.last_heartbeat);
//                 $("#gps_fixed").text(data.gps_fixed);
//                 $("#connection").text(data.connection)
//             };
//             Csocket.onmessage = function (event) {
//                 self.isHandling = false;
//                 try {
//                     if (event.data != "" && event.data != null && event.data != undefined) {
//                         var response = JSON.parse(event.data);
//                         if (response.hasOwnProperty("type")) {
//                             if (response.type == "update_statistic") {
//                                 Csocket.update_statistic(response.data);
//                             } else if (response.message == "draw routes") {

//                             }
//                         }
//                     }
//                 } catch (e) {
//                     console.log(response);
//                     console.log(e);
//                     console.log(event.data);
//                 }
//             };

//             Csocket.onerror = function (error) {
//                 console.log(error);
//                 console.log("Ошибка " + error.message);
//                 self.connected = false;
//             };
//             wsListener.send_message = function (message) {
//                 Csocket.send(JSON.stringify(message));
//             };
//         } catch (e) {
//             console.log(e)
//         }
//     }
//     var Csocket;
//     var intervalID = setInterval(function () {
//         if (self.connected == false) {
//         //} else {
//             self.connect();
//         }
//     }, 2000);


// })(window);
/* WebSocketMessages */
(function (window) {
    window.WebSocketMessages = function (arParams) {
        this.parameters = arParams;
        // this.update_statistic(0.3);
        // this.check_route_status(1);
        this.distance_checker(0.5);
    };
    window.WebSocketMessages.prototype.handle = function (event) {
        try {
            if (event.data != "" && event.data != null && event.data != undefined) {
                var response = JSON.parse(event.data);
                if (response.hasOwnProperty("type")) {
                    if (response.type == "update_statistic") {
                        pageBuilder.update_statistic(response.data);
                    } else if(response.type == "update_rtl_position"){
                        mapControl.updateRTLPosition(response.data);
                    } else if (response.type == "draw routes") {

                    } else if (response.type == "change_route_status") {

                        if (response.data.hasOwnProperty("uid")) {
                            for (id in window.wsListener.notDoneMessages) {
                                if (window.wsListener.notDoneMessages[id] == response.data.uid) {
                                    delete window.wsListener.notDoneMessages[id];
                                }
                            }
                            //.wsListener.notDoneMessages.remove(response.data.uid);
                            pageBuilder.change_route_status(response.data);
                        }

                    } else if (response.type == "event_notification"){
                        window.app.notification('info', response.data.name);
                        // console.log(response.data.name);
                        // console.log(app.notifications);
                    }
                    //console.log(response);
                }
            }
        } catch (e) {
            console.log(response);
            console.log(e);
            console.log(event.data);
        }
    }
    window.WebSocketMessages.prototype.update_statistic = function (timeout) {
        var updateInterval = setInterval(function () {
            if (window.wsListener.connected == true) {
                window.wsListener.send_message({type: "update_statistic"});
            }
            // else {
            //     clearInterval(updateInterval);
            //     window.WebSocketMessages.update_statistic();
            // }
            // обновляем показатели коптера в панели
        }, timeout * 1000);
    }
    window.WebSocketMessages.prototype.check_route_status = function (timeout) {
        setInterval(function () {
            if (wsListener.connected == true) {
                if ($('.routes_tab.active').attr('route_uid') != undefined) {
                    if (app.active_copter != 0) {
                        window.wsListener.send_message({
                            type: 'check_route_status',
                            data: {
                                uid: $('.routes_tab.active').attr('route_uid'),
                                copter_id: $('.routes_tab.active').attr('data-copter-id'),
                                cancelling: ControlPane.cancelling
                            }
                        });
                    }
                }
            }
        }, timeout * 1000);
    }
    window.WebSocketMessages.prototype.distance_checker = function (timeout) {
        setInterval(function () {
            if (wsListener.connected == true) {
                pageBuilder.check_distance();
            }
        }, timeout * 1000);

    }

    window.WebSocketMessages.prototype.sender = function () {
        setInterval(function () {
            for (var i = 0; i < wsListener.notSendedMessages.length; i++) {
                if (wsListener.notSendedMessages[i] != undefined) {
                    if (wsListener.notDoneMessages.findIndex(x => x === wsListener.notSendedMessages[i].uid) == -1) { // Значение не найдено в списке отправленных
                        if (wsListener.connected == true) {
                            wsListener.notSendedMessages[i].timestamp = Math.floor(Date.now() / 1000);
                            wsListener.send_message(wsListener.notSendedMessages[i]);
                            wsListener.notDoneMessages[wsListener.notDoneMessages.length] = wsListener.notSendedMessages[i].uid;
                            delete wsListener.notSendedMessages[i];
                            if (wsListener.notSendedMessages.length > 0) {
                                try {
                                    if (wsListener.notSendedMessages[0] == undefined) {
                                        wsListener.notSendedMessages = [];
                                    }
                                } catch (e) {

                                }
                            }
                        }

                    }
                }
            }
            for (copter_id in ControlPane.copters) {
                var copter = ControlPane.copters[copter_id];
                if (copter.properties.timestamp != undefined) {
                    if (copter.properties.timestamp.day != new Date().getDate()) {
                        $("#copter_stats_" + copter_id).find("#connection").text("False");
                    } else {
                        if (new Date().getHours() - (copter.properties.timestamp.hour) > 0) {
                            $("#copter_stats_" + copter_id).find("#connection").text("False");
                        } else {
                            if (new Date().getMinutes() - copter.properties.timestamp.minute > 0) {
                                $("#copter_stats_" + copter_id).find("#connection").text("False");
                            } else {
                                if (new Date().getSeconds() - copter.properties.timestamp.second > 20) {
                                    $("#copter_stats_" + copter_id).find("#connection").text("False");
                                } else {
                                    $("#copter_stats_" + copter_id).find("#connection").text("True");
                                }
                            }
                        }
                    }
                } else {
                    $("#copter_stats_" + copter_id).find("#connection").text("False");
                }

            }
        }, 500);
    }
    window.WebSocketMessages.prototype.UploadRoute = function (copter_id, route) {
        var self = wsListener;
        var route_uid = route.uid;
        $('.routes_tab[data-copter-id="' + copter.id + '"]').attr('route_uid', route_uid);
        self.notSendedMessages[self.notSendedMessages.length] = {
            uid: route_uid,
            type: "upload_route",
            copter_id: copter_id,
            is_done: false,
            is_sync: false,
            route: route,
            status: "0"
        };
    }
    window.WebSocketMessages.prototype.addCommand = function (command) {
        var self = wsListener;
        var route_uid = command.route_uid;
        self.notSendedMessages[self.notSendedMessages.length] = {
            uid: ControlPane.uid(),
            type: "add_command",
            copter_id: copter_id,
            is_done: false,
            is_sync: false,
            command: command,
            route_uid: route_uid,
            status: "1"
        };
    }
})(window);
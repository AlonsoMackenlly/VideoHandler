var MAJOR_AXIS = 6378137.0; //meters
var MINOR_AXIS = 6356752.3142; //meters
var MAJOR_AXIS_POW_2 = Math.pow(MAJOR_AXIS, 2); //meters
var MINOR_AXIS_POW_2 = Math.pow(MINOR_AXIS, 2); //meters
/*
$gps_1['lat'] - latitude (широта)
$gps_1['lon'] - longitude (долгота)
$gps_1['point_elevation'] (высота точки) // == 0 if this is sea. but must be defined!
*/
Math.radians = function (degrees) {
    return degrees * Math.PI / 180;
};

// Converts from radians to degrees.
Math.degrees = function (radians) {
    return radians * 180 / Math.PI;
};

function get_distance_between_2_points(gps_1, gps_2, decart = false) {
    if (decart == false) {
        var true_angle_1 = get_true_angle(gps_1);
        var true_angle_2 = get_true_angle(gps_2);
        var point_radius_1 = get_point_radius(gps_1, true_angle_1);
        var point_radius_2 = get_point_radius(gps_2, true_angle_2);
        var earth_point_1_x = point_radius_1 * Math.cos(Math.radians(true_angle_1));
        var earth_point_1_y = point_radius_1 * Math.sin(Math.radians(true_angle_1));
        var earth_point_2_x = point_radius_2 * Math.cos(Math.radians(true_angle_2));
        var earth_point_2_y = point_radius_2 * Math.sin(Math.radians(true_angle_2));
        var x = get_distance_between_2_points({
            'lat': earth_point_1_x,
            'lon': earth_point_1_y
        }, {'lat': earth_point_2_x, 'lon': earth_point_2_y}, true);
        var y = Math.PI * ((earth_point_1_x + earth_point_2_x) / 360) * (gps_1['lon'] - gps_2['lon']);
        return Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2));
    } else {
        return Math.sqrt(Math.pow((gps_1['lat'] - gps_2['lat']), 2) + Math.pow((gps_1['lon'] - gps_2['lon']), 2));
    }
}

//returns degree's decimal measure, getting degree, minute and second
function get_decimal_degree(deg = 0, min = 0, sec = 0) {
    return (deg < 0) ? (-1 * (Math.abs(deg) + (Math.abs(min) / 60) + (Math.abs(sec) / 3600))) : (Math.abs(deg) + (Math.abs(min) / 60) + (Math.abs(sec) / 3600));
}

// get point, returns true angle
function get_true_angle(gps) {
    return Math.atan(((MINOR_AXIS_POW_2 / MAJOR_AXIS_POW_2) * Math.tan(Math.radians(gps['lat'])))) * 180 / Math.PI;
}

//get point and true angle, returns radius of small circle (radius between meridians)
function get_point_radius(gps, true_angle) {
    return (1 / Math.sqrt((Math.pow(Math.cos(Math.radians(true_angle)), 2) / MAJOR_AXIS_POW_2) + (Math.pow(Math.sin(Math.radians(true_angle)), 2) / MINOR_AXIS_POW_2))) + gps['point_elevation'];
}

function check_lat(lat) {
    if (lat >= 0 && lat <= 90) {
        return 'north';
    } else if (lat >= -90 && lat <= 0) {
        return 'south';
    }
    return false;
}

function check_lon(lon) {
    if (lon >= 0 && lon <= 180) {
        return 'east';
    } else if (lon >= -180 && lon <= 0) {
        return 'west';
    }
    return false;
}

/* Page builder */
(function (window) {
    window.pageBuilder = {};
    window.createNotification = function (str, time) {
        let notId = new Date().getTime();
        let html = '<div id="notification_' + notId + '" class="notification">' + str + '</div>';
        $(document.body).append(html);
        $('#notification_' + notId).css('opacity', '0.7');
        setTimeout(function () {
            $('#notification_' + notId).animate({
                opacity: 0
            }, 1000);
        }, time * 1000);
    }
    window.pageBuilder.check_distance = function () {
        if (wsListener.connected == true) {
            var point_btns = $('.routes_tab.active .routes_tab_points .point');

            $(point_btns).each(function (index, point_element) {
                if ($(point_element).attr('data-status') == '2') {

                    setTimeout(function () {
                        try {
                            //$('.routes_tab.active .routes_tab_points .point_procent').remove();
                            //procent = document.createElement('p');
                            //$(procent).addClass('point_procent');

                            var target_point = {
                                lat: parseFloat($(point_element).attr('data-lat')),
                                lon: parseFloat($(point_element).attr('data-lon')),
                                point_elevation: 0 // TODO: "point_elevation: 0" переделать в дальнейшем
                            }
                            var copter_id = $('.routes_tab.active').attr('data-copter-id');
                            if (index == 0) {
                                issetObjectsRTL = false;
                                coordinatesRTL = [];
                                window.Ymap.geoObjects.each(function (object) {
                                    if (object.properties.__type == 'rtl') {
                                        if (object.properties.hasOwnProperty('__copter_id')) {
                                            if (object.properties.__copter_id == copter_id) {
                                                issetObjectsRTL = true;
                                                coordinatesRTL = object.geometry.getCoordinates();
                                            }
                                        }
                                    }
                                });
                                if (issetObjectsRTL == true) {
                                    var current_point_copter = {
                                        lat: ControlPane.copters[copter_id].properties.coordinates_lat,
                                        lon: ControlPane.copters[copter_id].properties.coordinates_lon,
                                        point_elevation: 0 // TODO: "point_elevation: 0" переделать в дальнейшем
                                    };
                                    var current_point = {
                                        lat: coordinatesRTL[0],
                                        lon: coordinatesRTL[1],
                                        point_elevation: 0 // TODO: "point_elevation: 0" переделать в дальнейшем
                                    }
                                    var current_distance = get_distance_between_2_points(current_point, target_point, false);
                                    current_distance = Math.round(current_distance);
                                    var current_distance = get_distance_between_2_points(current_point_copter, target_point, false);
                                    var all_distance = get_distance_between_2_points(current_point, target_point, false);
                                    var proc = current_distance / all_distance * 100;
                                    var proc_ = 100 - Math.round(proc, 1);
                                    $($(point_element).find('.progress-bar-fill')).css('width', proc_ + '%');
                                }

                                //$(procent).text(distance + " м.");
                            } else {
                                var current_point_copter = {
                                    lat: ControlPane.copters[copter_id].properties.coordinates_lat,
                                    lon: ControlPane.copters[copter_id].properties.coordinates_lon,
                                    point_elevation: 0 // TODO: "point_elevation: 0" переделать в дальнейшем
                                }
                                var current_point = {
                                    lat: parseFloat($($(point_btns)[index - 1]).attr('data-lat')),
                                    lon: parseFloat($($(point_btns)[index - 1]).attr('data-lon')),
                                    point_elevation: 0 // TODO: "point_elevation: 0" переделать в дальнейшем
                                }
                                var current_distance = get_distance_between_2_points(current_point_copter, target_point, false);
                                var all_distance = get_distance_between_2_points(current_point, target_point, false);
                                var proc = current_distance / all_distance * 100;
                                var proc_ = 100 - Math.round(proc, 1);
                                $($(point_element).find('.progress-bar-fill')).css('width', proc_ + '%');
                                //$(procent).text( proc_+ " %");

                            }
                            //$(procent).insertBefore($(point_element));
                        } catch (e) {
                            // console.log(e);
                        }

                    }, 1000);
                }
            });
            //get_distance_between_2_points({lat:53.539602,lon: 49.264855,point_elevation:0}, {lat:53.533715,lon: 49.319855,point_elevation:0}, false);
        }
    }


// TODO: переместить в page_builder
    window.pageBuilder.update_statistic = function (data) {
        // console.log(" ***************************** < copter " + data.copter_id + " > ***************************");
        // console.log('voltage = ' + app.copters[data.copter_id].properties.battery_voltage);
        // console.log('voltage = ' + app.copters[data.copter_id].properties.battery_voltage);
        // console.log('coordinates_lat = ' + data.coordinates_lat);
        // console.log('coordinates_lon = ' + data.coordinates_lon);
        // console.log(" ***************************** </ copter " + data.copter_id + " > ***************************");
        console.log(data.copter_id);
        app.copters[data.copter_id].properties = {};
        app.copters[data.copter_id].properties.coordinates_alt = data.coordinates_alt;
        app.copters[data.copter_id].properties.coordinates_lat = data.coordinates_lat;
        app.copters[data.copter_id].properties.coordinates_lon = data.coordinates_lon;
        app.copters[data.copter_id].properties.air_speed = data.air_speed;
        app.copters[data.copter_id].properties.battery_level = data.battery_level;
        app.copters[data.copter_id].properties.battery_voltage = data.battery_voltage;
        ControlPane.copters[data.copter_id].properties.connection = data.connection;
        app.copters[data.copter_id].properties.gps_fixed = data.gps_fixed;
        app.copters[data.copter_id].properties.ground_speed = data.ground_speed;
        app.copters[data.copter_id].properties.is_armable = data.is_armable;
        app.copters[data.copter_id].properties.is_armed = data.is_armed;
        app.copters[data.copter_id].properties.last_heartbeat = data.last_heartbeat;
        app.copters[data.copter_id].properties.mode = data.mode;
        app.copters[data.copter_id].properties.status = data.status;
        app.copters[data.copter_id].properties.timestamp = data.history_timestamp;

        //if

        // if (data.history_timestamp.day != new Date().getDate()) {
        //     $(stats_pane).find("#connection").text("False");
        // } else {
        //     if (new Date().getHours() - (data.history_timestamp.hour) > 0) {
        //         $(stats_pane).find("#connection").text("False");
        //     } else {
        //         if (new Date().getMinutes() - data.history_timestamp.minute > 0) {
        //             $(stats_pane).find("#connection").text("False");
        //         } else {
        //             if (new Date().getSeconds() - data.history_timestamp.second > 20) {
        //                 $(stats_pane).find("#connection").text("False");
        //             } else {
        //                 $(stats_pane).find("#connection").text("True");
        //             }
        //         }
        //     }
        // }


    };
    window.pageBuilder.UpdateRoute = function (copter_id, route) {
        var route_tab = $('.routes_tab[data-copter-id="' + copter_id + '"]');
        if ($(route_tab).find('.routes_tab_points div.point').length == 0) {

        } else {

        }
    }
    window.pageBuilder.change_route_status = function (message) {
        //if (((app.copters[message['copter_id']].route.status == "4" || app.copters[message['copter_id']].route.status == "2") && message['status'] == '0') || app.copters[message['copter_id']].route.status != message['status']) {
        if (message['needRedraw'] == true){
            app.deleteMapObjectsByType('route', parseInt(message['copter_id']));
            app.deleteMapObjectsByType('point', parseInt(message['copter_id']));
            MapObjectTemplate.build_route(message['points'], parseInt(message['copter_id']));
            // mapControl.updateRoutePoliline(message['points'], parseInt(message['copter_id']));
        }
        if (app.copters[message['copter_id']].route.uid != message['uid']){
            app.deleteMapObjectsByType('point', message['copter_id']);
            app.deleteMapObjectsByType('route', message['copter_id']);
        }
        app.copters[message['copter_id']].route.uid = message['uid'];
        app.copters[message['copter_id']].route.status = message['status'];
        if (message['status'] == "1" || message['status'] == 1) {
            mapControl.drawRTL(app.copters[message['copter_id']]);
        }
        issetRoute = false;
        window.Ymap.geoObjects.each(function (object) {
            if (object.properties.__type == 'point' && object.properties.__copter_id == message['copter_id']) {
                issetRoute = true;
            }
        });
        if (issetRoute == false) {
            MapObjectTemplate.build_route(message['points'], message['copter_id']);
        }
        for (var component in app.$children) {
            if (app.$children[component].$data.__name == 'routes-tab') {
                app.$children[component].$emit('enableAllBtns', message['copter_id']);
            }
        }


        app.clearCommands(parseFloat(message['copter_id']));
        for (point_id in message['points']) {
            let point = message['points'][point_id];
            let copter = app.copters[message['copter_id']];
            let route = copter.route;

            Vue.set(app.copters[message['copter_id']].route.commands, message['points'][point_id]['order'], message['points'][point_id]);
            let point_original = app.copters[message['copter_id']].route.commands[message['points'][point_id]['order']];
            if (point_original.hasOwnProperty('coordinates')) {
                if (point_original.coordinates != point['coordinates']) {
                    point_original.coordinates = point['coordinates'];
                }
                if (point_original.status != point['status']) {
                    point_original.status = point['status'];
                }
                if (point_original.type != point['type']) {
                    point_original.type = point['type'];
                }
                if (point_original.uid != point['uid']) {
                    point_original.uid = point['uid'];
                }
                if (point_id != point['order']) {
                    Vue.set(app.copters[message['copter_id']].route.commands, point_id, point['order']);
                }
            }
        }
        //}


    }
})
(window);
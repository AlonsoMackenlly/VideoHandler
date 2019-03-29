/* mapDrawing */
(function (window) {
    if (!Object.keys) {
        Object.keys = function (obj) {
            var keys = [],
                k;
            for (k in obj) {
                if (Object.prototype.hasOwnProperty.call(obj, k)) {
                    keys.push(k);
                }
            }
            return keys;
        };
    }
    window.mapControl = function (arParams) {
        this.arParams = arParams;
        if (!Object.keys) {
            Object.keys = function (obj) {
                var keys = [],
                    k;
                for (k in obj) {
                    if (Object.prototype.hasOwnProperty.call(obj, k)) {
                        keys.push(k);
                    }
                }
                return keys;
            };
        }
        this.Init();
    };
    window.mapControl.prototype.setDragEndCallBack = function (params) {
        var placemark = params['placemark'];
        var copter_id = params['copter_id'];
        var is_rtl = params['is_rtl'];
        var is_command = params['is_command'];
        placemark.events.add('dragend', function (e) {
            // координаты можно получить из
            var coordinates = placemark.geometry.getCoordinates();
            if (is_rtl == true){
                window.wsListener.notSendedMessages[window.wsListener.notSendedMessages.length] = {
                    uid: ControlPane.uid(),
                    type: 'set_rtl',
                    data: {
                        copter_id: copter_id,
                        coordinates: coordinates
                    }
                };
            }
            else if (is_command == true){
                console.log(placemark.events);

            }



        });

    }
    window.mapControl.prototype.Init = function () {
        var self = this;
        ymaps.ready(function () {
            window.Ymap.events.add('click', function (e) {
                self.checkDrawing(e);
                self.checkAddCommand(e);
            });
            for (base_id in window.ControlPane.bases) {
                window.ControlPane.bases[base_id].template_parts.circle.events.add('click', function (e) {
                    self.checkDrawing(e);

                });
            }
        });

    }
    window.mapControl.prototype.drawRTL = function (copter_object) {
        issetObjectsRTL = false;
        window.Ymap.geoObjects.each(function (object) {
            if (object.properties.__type == 'rtl') {
                if (object.properties.hasOwnProperty('__copter_id')) {
                    if (object.properties.__copter_id == copter_object.id) {
                        issetObjectsRTL = true;
                    }
                }
            }
        });
        if (issetObjectsRTL == false) {
            copter_object.template_parts.RTL = new ymaps.Placemark([copter_object.properties.coordinates_lat, copter_object.properties.coordinates_lon], {
                hintContent: '',
                balloonContent: '',
                content: ''
            }, {
                draggable: true,
                // balloonContentLayout: copter_object.templateParts.BalloonContentBodyLayout,
                // Опции.
                // Необходимо указать данный тип макета.
                iconLayout: 'default#image',
                // Своё изображение иконки метки.
                iconImageHref: '/media/base.png',
                // Размеры метки.
                iconImageSize: [45, 45],
                // Смещение левого верхнего угла иконки относительно
                // её "ножки" (точки привязки).
                iconImageOffset: [-22.5, -22.5] // * вручную подобрано от ширины и высоты картинки *
            });
            copter_object.template_parts.RTL.properties.__type = "rtl";
            copter_object.template_parts.RTL.properties.__copter_id = copter_object.id;

            window.Ymap.geoObjects.add(copter_object.template_parts.RTL);
            window.wsListener.notSendedMessages[window.wsListener.notSendedMessages.length] = {
                uid: ControlPane.uid(),
                type: 'set_rtl',
                data: {
                    copter_id: copter_object.id,
                    coordinates: [copter_object.properties.coordinates_lat, copter_object.properties.coordinates_lon]
                }
            };
            params = {
                placemark: copter_object.template_parts.RTL,
                copter_id: copter_object.id,
                is_rtl: true
            }
            this.setDragEndCallBack(copter_object.template_parts.RTL, copter_object.id);
        }

    }
    window.mapControl.prototype.startDrawing = function (start_point, copter_id) {
        console.log(app.__drawing_type);
        if (app.__drawing_type == '' || app.__drawing_type == undefined){
            var polyline = new ymaps.Polyline([start_point], {
                hintContent: "Ломаная"
            }, {
                maxPoints: 5,
                strokeColor: '#008db6',
                strokeWidth: 3,
                strokeStyle: [0, 0, 'dash'],
                // Первой цифрой задаем длину штриха. Второй — длину разрыва.
                strokeStyle: '5 2',
                editorMenuManager: function (items, polygon) {
                    // items.push({
                    //     title: "Тип точки",
                    //     onClick: function () {
                    //     	polygon.geometry._type = "";
                    //         console.log(polygon);
                    //     }
                    // });
                    items[1].onClick = function (event) { // Редактирование окончено
                        polyline.editor.stopEditing();
                        app.is_drawing = false;
                        var coordinates = polyline.geometry.getCoordinates();
                        if (coordinates != undefined) {
                            var len = coordinates.length;
                            if (len > 0) {

                                window.MapObjectTemplate.build_route(coordinates, app.active_copter);
                            }
                        }
                        copter = app.copters[app.active_copter];
                        Vue.set(app.copters[copter_id].route, 'commands', {});
                        for (var i in coordinates) {
                            Vue.set(app.copters[copter_id].route.commands, i, {
                                coordinates: coordinates[i],
                                uid: ControlPane.uid(),
                                type: 'waypoint',
                                status: "0",
                                id: 'no',
                                drone_id: window.app.active_copter
                            });
                        }
                        var uid = ControlPane.uid();
                        copter.route.uid = uid;
                        WebSocketMessages.UploadRoute(copter.id, copter.route);

                    }
                    return items;
                }
            });
            polyline.events.add('editorstatechange', function (e) {
                var state = e.get('target').editor.state;
            });
            polyline.properties.__type = "route";
            polyline.properties.__copter_id = copter_id;
            window.Ymap.geoObjects.add(polyline);
            polyline.editor.startEditing();
            // Включение режима редактирования
            polyline.editor.startDrawing();
        }
        else if (app.__drawing_type == 'waypoint'){
            var issetCommands = false;
            var img = "/media/point_start.png";
            var command_obj = {};
            if (Object.keys(app.copters[copter_id].route.commands).length > 0){
                issetCommands = true;
                img = "/media/point.png";
                var max_order = 0;
                Object.keys(app.copters[copter_id].route.commands).forEach(function(order){
                   if (order > max_order){
                       max_order = order;
                   }
                });
                route_uid = app.copters[copter_id].route.commands[parseInt(max_order)].route_uid;
                max_order = parseInt(max_order) + 10;

                command_obj = {
                    coordinates: start_point,
                    drone_id: copter_id,
                    id: 0,
                    order: max_order,
                    status: "0",
                    type: 'waypoint',
                    uid: ControlPane.uid(),
                    route_uid: route_uid
                };
            }
            else{
                command_obj = {
                    coordinates: start_point,
                    drone_id: copter_id,
                    id: 0,
                    order: 10,
                    status: "0",
                    type: 'waypoint',
                    uid: ControlPane.uid()
                };
                Vue.set(app.copters[copter_id].route.commands, command_obj.order, command_obj);
            }
            // var placemark = new ymaps.Placemark(start_point, {
            //     hintContent: 'Точка',
            //     balloonContent: 'Точка маршрута',
            //     content: ''
            // }, {
            //     //balloonContentLayout: self.templateParts.BalloonContentBodyLayout,
            //     // Опции.
            //     // Необходимо указать данный тип макета.
            //     iconLayout: 'default#image',
            //     draggable: true,
            //     // Своё изображение иконки метки.
            //     iconImageHref: img,
            //     // Размеры метки.
            //     iconImageSize: [35, 35],
            //     // Смещение левого верхнего угла иконки относительно
            //     // её "ножки" (точки привязки).
            //     iconImageOffset: [-17.5, -17.5] // * вручную подобрано от ширины и высоты картинки *
            // });
            // placemark.properties.__type = "point";
            // placemark.properties.__copter_id = copter_id;
            // placemark.properties.__command_uid = 0;
            // window.Ymap.geoObjects.add(placemark);
            // this.setDragEndCallBack({
            //     'placemark': placemark,
            //     'is_command': true,
            //     'copter_id': copter_id
            // });
            app.is_drawing = false;
            app.done_point_build_in_view(app.__drawing_type, copter_id);
            app.__drawing_type = '';
            // Vue.set(app.copters[copter_id].route.commands, command_obj.order, command_obj);
            this.updateRoute(command_obj);
        }
        else if (app.__drawing_type == 'roi'){

        }
    }
    window.mapControl.prototype.checkAddCommand = function (e) {
        if (!window.Ymap.balloon.isOpen()) {
            var coords = e.get('coords');
            var copter = window.app.copters[window.app.active_copter];
            if (copter.buildCommandSwitch == true) {
                route_len = Object.keys(copter.route).length;
                if (route_len > 0){
                    copter.route.commands["__roi__" + ControlPane.uid()] = {
                        coordinates:coords,
                        type: 'roi',
                        uid: ControlPane.uid(),
                        status: "0",
                        id: 'no',
                        drone_id: copter.id
                    };
                }
                else{
                    copter.route = {
                        drone_id: copter.id,
                        uid: ControlPane.uid(),
                        commands: {}
                    };
                    copter.route.commands["__roi__" + ControlPane.uid()] = {
                        coordinates:coords,
                        type: 'roi',
                        uid: ControlPane.uid(),
                        status: "0",
                        id: 'no',
                        drone_id: copter.id
                    };
                }

                copter.buildCommandSwitch = false;
                window.pageBuilder.roi_waypoint_add();
            }
        }
    }
    window.mapControl.prototype.checkDrawing = function (e) {
        if (!window.Ymap.balloon.isOpen()) {
            var coords = e.get('coords');
            if (app.is_drawing == true) {
                var copter = window.app.copters[window.app.active_copter];
                if (copter.roiSwitch == false) {
                    route_len = Object.keys(copter.route).length;
                    var startPoint = coords;
                    this.startDrawing(startPoint, app.active_copter);
                }
            }

        } else {
            window.Ymap.balloon.close();
        }
    }
    window.mapControl.prototype.panToCopter = function (copter_id) {
        var copter = window.ControlPane.findCopterByID(copter_id);
        if (Object.keys(copter.properties).length > 0 && parseFloat(copter.properties.coordinates_lat) != 0 && parseFloat(copter.properties.coordinates_lon) != 0 ) {
            window.Ymap.panTo(
                [parseFloat(copter.properties.coordinates_lat), parseFloat(copter.properties.coordinates_lon)], {
                    duration: 1000,
                    zoom: 12,
                    checkZoomRange: true,
                    flying: true
                }
            ).then(function () {
                Ymap.setZoom(18, {duration: 1000});
            });
        }
    }
    window.mapControl.prototype.updateRTLPosition  = function(data){
        let rtl_obj = window.app.copters[data['copter_id']]['template_parts']['RTL'];
        rtl_obj.geometry.setCoordinates([data['coordinates'][0], data['coordinates'][1]]);
    }
    window.mapControl.prototype.updateRoute = function(command){
        if (app.copters[command.drone_id].route.uid == 0 || app.copters[command.drone_id].route.status == -1){
            app.copters[command.drone_id].route.uid = ControlPane.uid();
            WebSocketMessages.UploadRoute(app.copters[command.drone_id].id, app.copters[command.drone_id].route);
        }
        else{
            if (Object.keys(app.copters[command.drone_id].route.commands).length > 0){
                WebSocketMessages.addCommand(command);
            }
        }
    }
})(window);


// let MyIconContentLayout = ymaps.templateLayoutFactory.createClass(
//     '<div style="color: #FFFFFF; font-weight: bold;"><i class="far fa-eye" style="font-size: 40px;color: black;text-shadow: 0px 0px 14px white, 0px 0px 45px white, 0px 0px 47px white;"></i></div>'
// );
// console.log(object.home_location);
// var RTL = new ymaps.Placemark([object.home_location[0], object.home_location[1]], {
//     hintContent: '',
//     balloonContent: '',
//     content: ''
// }, {
//     zIndex:100,
//     draggable: true,
//     // balloonContentLayout: copter_object.templateParts.BalloonContentBodyLayout,
//     // Опции.
//     // Необходимо указать данный тип макета.
//     iconLayout: 'default#imageWithContent',
//     iconContentLayout: MyIconContentLayout,
//     // Своё изображение иконки метки.
//     iconImageHref: '#', // media/base.png
//     iconImageSize: [45, 45],
//     // Смещение левого верхнего угла иконки относительно
//     // её "ножки" (точки привязки).
//     iconImageOffset: [-22.5, -22.5] // * вручную подобрано от ширины и высоты картинки *
// });

// ***************************************************************************************************
// window.Ymap.balloon.open(coords, {
//     contentHeader: 'Событие!',
//     contentBody: '<p>Кто-то щелкнул по карте.</p>' +
//         '<p>Координаты щелчка: ' + [
//             coords[0].toPrecision(6),
//             coords[1].toPrecision(6)
//         ].join(', ') + '</p>',
//     contentFooter: '<sup>Щелкните еще раз</sup>'
// });
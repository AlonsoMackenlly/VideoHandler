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
    window.mapControl.prototype.setDragEndCallBack = function (placemark, copter_id) {
        placemark.events.add('dragend', function (e) {
            // координаты можно получить из
            var coordinates = placemark.geometry.getCoordinates();
            window.wsListener.notSendedMessages[window.wsListener.notSendedMessages.length] = {
                uid: ControlPane.uid(),
                type: 'set_rtl',
                data: {
                    copter_id: copter_id,
                    coordinates: coordinates
                }
            };
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
        console.log(issetObjectsRTL);
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
            window.mapControl.setDragEndCallBack(copter_object.template_parts.RTL, copter_object.id);
        }

    }
    window.mapControl.prototype.startDrawing = function (start_point, copter_id) {
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
                    ControlPane.is_drawing = false;
                    var coordinates = polyline.geometry.getCoordinates();
                    if (coordinates != undefined) {
                        var len = coordinates.length;
                        if (len > 0) {
                            window.MapObjectTemplate.build_route(coordinates, app.active_copter);
                        }
                    }
                    copter = app.copters[app.active_copter];
                    copter.route.__commands = {};
                    for (var i in coordinates) {
                        copter.route.__commands[i] = {
                            coordinates: coordinates[i],
                            uid: ControlPane.uid(),
                            type: 'waypoint',
                            status: "0",
                            id: 'no',
                            drone_id: window.app.active_copter
                        };
                    }
                    console.log(copter.route.__commands);
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
    window.mapControl.prototype.checkAddCommand = function (e) {
        if (!window.Ymap.balloon.isOpen()) {
            var coords = e.get('coords');
            var copter = window.app.copters[window.app.active_copter];
            if (copter.buildCommandSwitch == true) {
                route_len = Object.keys(copter.route).length;
                if (route_len > 0){
                    console.log(copter.route);
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
            if (ControlPane.is_drawing == true) {
                var copter = window.app.copters[window.app.active_copter];
                if (copter.roiSwitch == false) {
                    route_len = Object.keys(copter.route).length;
                    var startPoint = coords;
                    this.startDrawing(startPoint, app.active_copter);
                }


            }
            // window.Ymap.balloon.open(coords, {
            //     contentHeader: 'Событие!',
            //     contentBody: '<p>Кто-то щелкнул по карте.</p>' +
            //         '<p>Координаты щелчка: ' + [
            //             coords[0].toPrecision(6),
            //             coords[1].toPrecision(6)
            //         ].join(', ') + '</p>',
            //     contentFooter: '<sup>Щелкните еще раз</sup>'
            // });
        } else {
            window.Ymap.balloon.close();
        }
    }
    window.mapControl.prototype.panToCopter = function (copter_id) {
        var copter = window.ControlPane.findCopterByID(copter_id);
        if (Object.keys(copter.properties).length > 0 && copter.properties.coordinates_lat != undefined && copter.properties.coordinates_lon != undefined) {
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
    window.mapControl.prototype.updateRTLPosition = function(data){
        let rtl_obj = window.app.copters[data['copter_id']].template_parts.RTL;
        rtl_obj.geometry.setCoordinates([data['coordinates'][0], data['coordinates'][1]]);
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
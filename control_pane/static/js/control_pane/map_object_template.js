/* MapObjectTemplate */
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
    window.MapObjectTemplate = {
        templateParts: {
            BalloonContentBodyLayout: '',
            baloonContent: '',
            placemark: '',
            circle: ''
        }
    };
    window.MapObjectTemplate.build_route = function (points, copter_id) {
        var i = 0;
        geo = [];
        console.log(points);
        for (id in points) {
            var img = "/media/point.png";
            if (i == 0) {
                var img = "/media/point_start.png";
            }
            if (points[id].hasOwnProperty('coordinates')){
                geo.push(points[id].coordinates);
            }
            else if (points[id].hasOwnProperty('geo')){
                geo.push(points[id].geo);
            }
            else{
                geo.push(points[id]);
            }
            var placemark = new ymaps.Placemark(geo[geo.length - 1], {
                hintContent: 'Точка',
                balloonContent: 'Точка маршрута',
                content: ''
            }, {
                //balloonContentLayout: self.templateParts.BalloonContentBodyLayout,
                // Опции.
                // Необходимо указать данный тип макета.
                iconLayout: 'default#image',
                draggable: true,
                // Своё изображение иконки метки.
                iconImageHref: img,
                // Размеры метки.
                iconImageSize: [35, 35],
                // Смещение левого верхнего угла иконки относительно
                // её "ножки" (точки привязки).
                iconImageOffset: [-17.5, -17.5] // * вручную подобрано от ширины и высоты картинки *
            });

            placemark.properties.__type = "point";
            placemark.properties.__copter_id = copter_id;
            placemark.properties.__command_uid = 0;
            window.Ymap.geoObjects.add(placemark);
            mapControl.setDragEndCallBack({
                'placemark': placemark,
                'is_command': true,
                'copter_id': copter_id
            });
            i++;
        }
        var polyline = new ymaps.Polyline(geo, {
            hintContent: "Ломаная"
        }, {
            maxPoints: 5,
            strokeColor: '#008db6',
            strokeWidth: 3,
            strokeStyle: [0, 0, 'dash'],
            // Первой цифрой задаем длину штриха. Второй — длину разрыва.
            strokeStyle: '5 2',
        });
        polyline.properties.__type = "route";
        polyline.properties.__copter_id = copter_id;

        window.Ymap.geoObjects.add(polyline);
    }
    window.MapObjectTemplate.Init = function (object) {
        var self = this;
        if (object.object_type == "base") {
            ymaps.ready(function () {
                // **********************************************************************************
                var circle = new ymaps.Circle([
                    // Координаты центра круга.
                    [object.properties.coordinates_lat, object.properties.coordinates_lon],
                    // Радиус круга в метрах.
                    4000
                ], {
                    // Описываем свойства круга.
                    // Содержимое балуна.
                    balloonContent: "Радиус круга - 10 км",
                    // Содержимое хинта.
                    hintContent: "Подвинь меня"
                }, {
                    hasBalloon: false,
                    hasHint: false,
                    openBalloonOnClick: false,
                    openEmptyHint: true,
                    openHintOnHover: false,
                    zIndexHover: -111,
                    // Задаем опции круга.
                    // Включаем возможность перетаскивания круга.
                    draggable: false,
                    // Цвет заливки.
                    // Последний байт (77) определяет прозрачность.
                    // Прозрачность заливки также можно задать используя опцию "fillOpacity".
                    //fillOpacity: 0,
                    fill: true,
                    fillColor: "#39c6e142",
                    // Цвет обводки.
                    strokeColor: "#008db6",
                    // Прозрачность обводки.
                    strokeOpacity: 0.6,
                    // Ширина обводки в пикселях.
                    strokeWidth: 3
                });
                // self.templateParts.placemark = new ymaps.Placemark([object.properties.coordinates_lat, object.properties.coordinates_lon], {
                //     hintContent: '',
                //     balloonContent: '',
                //     content: self.templateParts.baloonContent
                // }, {
                //     draggable: true,
                //     balloonContentLayout: self.templateParts.BalloonContentBodyLayout,
                //     // Опции.
                //     // Необходимо указать данный тип макета.
                //     iconLayout: 'default#image',
                //     // Своё изображение иконки метки.
                //     iconImageHref: '/media/base.png',
                //     // Размеры метки.
                //     iconImageSize: [45, 45],
                //     // Смещение левого верхнего угла иконки относительно
                //     // её "ножки" (точки привязки).
                //     iconImageOffset: [-22.5, -22.5] // * вручную подобрано от ширины и высоты картинки *
                // });
                // self.templateParts.placemark.properties.__type = "base";
                // window.Ymap.geoObjects.add(self.templateParts.placemark);
                circle.properties.__type = "base";
                window.Ymap.geoObjects.add(circle);
                object.template_parts.circle = circle;
                // **********************************************************************************
            });
        } else if (object.object_type == "copter") {
            ymaps.ready(function () {
                if (object.route.commands != undefined) {
                    var len = Object.keys(object.route.commands).length;
                    if (len > 0) {
                        self.build_route(object.route.commands, object.id);
                    }
                }
                if (object.home_location != "" && object.home_location != undefined) {
                    var RTL = new ymaps.Placemark([object.home_location[0], object.home_location[1]], {
                        hintContent: '',
                        balloonContent: '',
                        content: ''
                    }, {
                        zIndex: 100,
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
                    RTL.properties.__type = "rtl";
                    RTL.properties.__copter_id = object.id;
                    window.Ymap.geoObjects.add(RTL);
                    params = {
                        placemark: RTL,
                        copter_id: object.id,
                        is_rtl: true
                    }
                    window.mapControl.setDragEndCallBack(params);
                }
                var intervalID = setInterval(function () {
                    if (object.properties.coordinates_lat != undefined && object.properties.coordinates_lon != undefined) {
                        self.templateParts.BalloonContentBodyLayout = ymaps.templateLayoutFactory.createClass('$[properties.content]');
                        // TODO: Нужно довести до автоматизации, чтобы с помощью автоматизации можно было выбирать отображаемые опции, если такое потребуется
                        self.templateParts.baloonContent = '<div></div>';

                        self.templateParts.placemark = new ymaps.Placemark([object.properties.coordinates_lat, object.properties.coordinates_lon], {
                            hintContent: 'Собственный значок метки',
                            balloonContent: 'Это красивая метка',
                            content: self.templateParts.baloonContent
                        }, {
                            zIndex: 10,
                            balloonContentLayout: self.templateParts.BalloonContentBodyLayout,
                            // Опции.
                            // Необходимо указать данный тип макета.
                            iconLayout: 'default#image',
                            draggable: false,
                            // Своё изображение иконки метки.
                            iconImageHref: '/media/copter.png',
                            // Размеры метки.
                            iconImageSize: [45, 45],
                            // Смещение левого верхнего угла иконки относительно
                            // её "ножки" (точки привязки).
                            iconImageOffset: [-22.5, -22.5] // * вручную подобрано от ширины и высоты картинки *
                        });
                        self.templateParts.placemark.properties.__type = "copter";
                        window.Ymap.geoObjects.add(self.templateParts.placemark);


                        object.template_parts = {placemark: self.templateParts.placemark, RTL: RTL};
                        clearInterval(intervalID);
                    }
                });

            });
        }
    }
})(window);

// var startPoint = [53.539524, 49.265238];//res.geoObjects.get(0).geometry.getCoordinates();
//  // Движемся на северо-восток, азимут 45 градусов
//  // или pi/4 радиан.
// var azimuth = 90;
// console.log(azimuth);
// // Направление движения.
// var direction = [Math.cos(azimuth), Math.sin(azimuth)];
// // Путевая функция.
// var path = ymaps.coordSystem.geo.solveDirectProblem(startPoint, direction, 2500).pathFunction;
//
//  // Изобразим путь на карте с помощью меток,
// // проставленных через каждые 10 км.
//  for (var i = 0; i <= 20; i++) {
//      window.Ymap.geoObjects.add(new ymaps.Placemark(path(i/20).point));
//  }
//  setInterval(function(){
//  	window.Ymap.geoObjects.each(function (geoObject) {
//  		if (azimuth == 360){
//  			azimuth
// 		}
// 		geoObject.setPosition()
// 	});
// }, 1000);



Vue.component('copter-list-item', {
    props: ['copter_id', 'copter_name'],
    data: function () {
        return {
            __name: 'copter-list-item',
            active: false,
            __copter_id: this.copter_id,
        }
    },
    methods: {
        onSelectItem: function () {
            // TODO: disable 'active' property for all list, beside active list item
            for (var component_id in app.$children){
                if (app.$children[component_id].$data.__name == "copter-list-item"){
                    if (app.$children[component_id].$data.__copter_id != this.__copter_id){
                        app.$children[component_id].active = false;
                    }
                }
            }
            if (app.active_copter != this.copter_id) {
                app.active_copter = this.copter_id;
                this.active = true;
                window.mapControl.panToCopter(this.copter_id);
            } else {
                app.active_copter = 0;
                this.active = false;
            }
        },
        isActive: function () {
            if (this.active == true) {
                return true;
            } else {
                return false;
            }
        }
    },
    template: `
                <li class="collapsed copter-list-item" @click="onSelectItem" :class="{ active: isActive()}">
                    <img src="/media/copter.png" alt="" class="copter-icon">
                    <a href="javascript:void(0);"> {{ copter_name }}</a>
                </li>
            `
});


Vue.component('copter-bottom-sidebar-item', {
    props: {
        copter: Object,
        active_copter: Number
    },
    data: function () {
        return {
            __copter_id: this.copter.id,
            __name: 'copter-bottom-sidebar-item',
        }
    },
    methods: {
        isActive: function () {
            if (this.copter.id == this.active_copter) {
                return true;
            } else {
                return false;
            }
        }
    },
    template:
        `   
            <transition name="fade">
                <div :data-copter-id="copter.id" class="copter_stats" :class="{ active: isActive()}">
                    <div class="container-fluid">
                        <div class="col-4-stats">
                            <div class="row1">
                                <div class="col col1">
                                    <div class="statistic-value">
                                        <div class="first-child">
                                            <i class="fa fa-area-chart" aria-hidden="true"></i>
                                            Высота
                                        </div>
                                        <div>
                                            <div id="altitude">{{ copter.properties.coordinates_alt }}</div>
                                        </div>
                                    </div>
                                    <div class="statistic-value">
                                        <div class="first-child">
                                            <i class="fa fa-tachometer" aria-hidden="true"></i>
                                            Скорость
                                        </div>
                                        <div>
                                            <div id="speed">{{ copter.properties.ground_speed }}</div>
                                        </div>
                                    </div>
                                    <div class="statistic-value">
                                        <div class="first-child">
                                            <i class="fa fa-info" aria-hidden="true"></i>
                                            Состояние
                                        </div>
                                        <div>
                                            <div id="state">{{ copter.properties.status }}</div>
                                        </div>
                                    </div>
                                    <div class="statistic-value">
                                        <div class="first-child">
                                            <i class="fa fa-crosshairs" aria-hidden="true"></i>
                                            Режим
                                        </div>
                                        <div>
                                            <div id="mode">{{ copter.properties.mode }}</div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col col2">
                                    <div class="statistic-value">
                                        <div class="first-child">
                                            <i class="fa fa-bolt" aria-hidden="true"></i>
                                            Батарея
                                        </div>
                                        <div>
                                            <div id="battery_level">
                                                {{ copter.properties.battery_level }}
                                                %, {{ copter.properties.battery_voltage }} V
                                            </div>
                                        </div>
                                    </div>
    
                                    <div class="statistic-value">
                                        <div class="first-child">
                                            <i class="fa fa-heart" aria-hidden="true"></i>
                                            Последний отклик
                                        </div>
                                        <div>
                                            <div id="last_heartbeat">{{ copter.properties.last_heartbeat }}</div>
                                        </div>
                                    </div>
    
                                    <div class="statistic-value">
                                        <div class="first-child">
                                            <i class="fa fa-globe" aria-hidden="true"></i>
                                            Спутников зафиксировано
                                        </div>
                                        <div>
                                            <div id="gps_fixed">{{ copter.properties.gps_fixed }}</div>
                                        </div>
                                    </div>
                                    <div class="statistic-value">
                                        <div class="first-child">
                                            <i class="fa fa-wifi" aria-hidden="true"></i>
                                            Подключение
                                        </div>
                                        <div>
                                            <div id="connection">{{ copter.properties.connection }}</div>
                                        </div>
                                        <!-- <div>
                                            <div id="connection">Нет соединения</div>
                                        </div> -->
                                    </div>
    
                                </div>
    
                            </div>
                        </div>
    
    
                    </div>
                </div>
            </transition>
        `
});
Vue.component('copter-bottom-sidebar', {
    props: {
        copters: Object,
        active_copter: Number
    },
    data: function () {
        return {
            // __copter_id: this.copter.id,
            __name: 'copter-bottom-sidebar',
        }
    },
    methods: {
        isActive: function () {
            if (this.active_copter != 0) {
                return true;
            } else {
                return false;
            }
        }
    },
    template:
        `        
                <transition name="fade">
                    <div class="bottom-pane" :class="{ active: isActive()}">
                        <div class="panel drone-tab">
                            <div class="panel-body">
                                <copter-bottom-sidebar-item v-for="copter in copters" :key="'copter-bottom-sidebar-item-' + copter.id" :copter="copter" :active_copter="active_copter"></copter-bottom-sidebar-item>
                            </div>
                        </div>
                    </div>
                </transition>
            `
});

Vue.component('copter-menu', {
    props: {
        copter: Object,
        items: Array,
        active_copter: Number
    },
    data: function () {
        return {
            __copter_id: this.copter.id,
            __name: 'copter-menu',
        }
    },
    methods: {
        onSelectItem: function (event) {

        },
        getMenuItems: function () {
            return {
                // route_tab: 'Маршрут',
                history_tab: 'История'
            }
        },
        isActive: function () {
            if (this.copter.id == this.active_copter) {
                return true;
            } else {
                return false;
            }
        }
    },
    template: `
                <ul class="sub-menu copter_action_list" :class="{ active: isActive()}" :id="'copter_action_list_' + copter.id" @click="onSelectItem">
                    <li v-for="(item, key) in getMenuItems()" :data-name="key">{{ item }}</li>
                </ul>
            `
});

Vue.component('routes-tab', {
    props: {
        copter: Object,
        active_copter: Number
    },
    data: function () {
        return {
            __copter_id: this.copter.id,
            __name: 'routes-tab',
            disable_draw: false,
            disable_run: false,
            disable_rebuild: false,
            disable_rerun: false,
            disable_pause: false,
            disable_unpause: false,
            disable_cancel: false,
            toggle_roi: false,
            disable_btn_add_waypoint: false,
            disable_btn_add_roi: false
        }
    },
    mounted: function () {
        window.busEmitter.$emit('ComponentTransition');
    },
    created: function () {
        this.$on('enableAllBtns', function (copter_id) {
            if (copter_id == this.copter.id) {
                this.disable_draw = false;
                this.disable_run = false;
                this.disable_rebuild = false;
                this.disable_rerun = false;
                this.disable_pause = false;
                this.disable_unpause = false;
                this.disable_cancel = false;
            }
        })
    },
    methods: {
        isActive: function () {
            if (this.copter.id === this.active_copter) {
                return true;
            } else {
                return false;
            }
        },
        enableRerunButton: function () {
            this.disable_rerun = false;
        },
        route_action: function (event) {
            let self = this;
            var action = event.target.getAttribute('data-action');
            if (action === 'draw') {
                window.ControlPane.is_drawing = !window.ControlPane.is_drawing;

                self.disable_draw = !self.disable_draw;
                if (self.disable_draw === false) {
                    app.deleteMapObjectsByType('route', this.copter.id);
                    self.disable_btn_add_waypoint = false;
                    self.disable_btn_add_roi = false;
                } else {
                    self.disable_btn_add_waypoint = true;
                    self.disable_btn_add_roi = true;
                }
            } else if (action === 'run') {
                if (self.disable_run === false) {
                    self.disable_rebuild = false;
                    self.disable_draw = false;
                    self.disable_run = !self.disable_run;
                    window.wsListener.notSendedMessages[window.wsListener.notSendedMessages.length] = {
                        uid: this.copter.route.uid,
                        type: "run_route",
                        copter_id: this.copter.id,
                    };
                } else {
                    event.preventDefault();
                }
            } else if (action === 'cancel') {
                if (self.disable_cancel === false) {
                    self.disable_cancel = !self.disable_cancel;
                    window.wsListener.notSendedMessages[window.wsListener.notSendedMessages.length] = {
                        uid: this.copter.route.uid,
                        type: "cancel_route",
                        copter_id: this.copter.id,
                    };
                } else {
                    event.preventDefault();
                }
            } else if (action === 'pause') {
                if (self.disable_pause === false) {
                    self.disable_cancel = true;
                    self.disable_pause = true;
                    self.disable_unpause = false;
                    window.wsListener.notSendedMessages[window.wsListener.notSendedMessages.length] = {
                        uid: this.copter.route.uid,
                        type: "pause_route",
                        copter_id: this.copter.id,
                    };
                } else {
                    event.preventDefault();
                }
            } else if (action === 'unpause') {
                if (self.disable_unpause === false) {
                    self.disable_unpause = true;
                    self.disable_cancel = false;
                    self.disable_pause = false;
                    window.wsListener.notSendedMessages[window.wsListener.notSendedMessages.length] = {
                        uid: this.copter.route.uid,
                        type: "unpause_route",
                        copter_id: this.copter.id,
                    };
                } else {
                    event.preventDefault();
                }
            } else if (action === 'rebuild') {
                if (self.disable_rebuild == false) {
                    self.disable_rebuild = true;
                    this.disable_draw = true;
                    this.disable_run = false;
                    window.ControlPane.is_drawing = !window.ControlPane.is_drawing;
                    app.copters[this.copter.id].route.status = -2;
                    app.deleteMapObjectsByType('route', this.copter.id);
                    app.deleteMapObjectsByType('point', this.copter.id);

                }
            } else if (action == 'rerun') {
                this.disable_rerun = true;
                window.wsListener.notSendedMessages[window.wsListener.notSendedMessages.length] = {
                    uid: this.copter.route.uid,
                    type: "rerun_route",
                    copter_id: this.copter.id,
                };

                this.disable_cancel = false;
            }
        },
        toggleCommands: function(){
            $(this.$refs.btn_group).slideToggle();
        }
    },
    template:
        `
            <div class="routes_tab" :class="{ active: isActive()}"
                                    :data-copter-id="copter.id"
                                    :route_uid="copter.route.uid"
                                    :data-status="copter.route.status">
                <div class="routes_tab_title">
                    Управление маршрутом
                </div>
                <div class="routes_tab_buttons">
                    <template v-if="copter.route.status == '-1'">
                            <div v-if="disable_draw === false" class="btn btn_base btn-primary build_route main_btn" data-action="draw" @click="route_action">Построить маршрут <i class="fas fa-route"></i></div>
                            <div v-else class="btn btn_base btn-danger build_route main_btn" data-action="draw"  @click="route_action">Отмена <i class="far fa-times-circle"></i></div>
                            <!--<div v-else-if="disable_draw === true && copter.route.status == '-1'" class="btn btn_base btn-primary build_route main_btn" data-action="draw" @click="route_action" disabled>Построить маршрут <i class="fas fa-route"></i></div>-->
                    </template>
                    <template v-else>
                        <template v-if="copter.route.status == '-2'">
                                <div v-if="disable_draw === false" class="btn btn_base btn-primary build_route main_btn" data-action="draw" @click="route_action">Построить маршрут <i class="fas fa-route"></i></div>
                                <div v-else class="btn btn_base btn-danger build_route main_btn" data-action="draw"  @click="route_action">Отмена <i class="far fa-times-circle"></i></div>
                                <!--<div v-else-if="disable_draw === true && copter.route.status == '-1'" class="btn btn_base btn-primary build_route main_btn" data-action="draw" @click="route_action" disabled>Построить маршрут <i class="fas fa-route"></i></div>-->
                        </template>
                        <template v-else-if="copter.route.status == '0'">
                            <div class="btn btn_base btn-primary build_route main_btn" data-action="run" :disabled="disable_run" @click="route_action">Запустить <i
                                    class="far fa-play-circle"></i></div>
                        </template>
                        <template v-else-if="copter.route.status == '1'">
                            {{ enableRerunButton() }}
                            <div class="btn btn_base btn-danger build_route main_btn" data-action="cancel" :disabled="disable_cancel" @click="route_action">Отменить
                                    маршрут <i class="far fa-times-circle"></i></div>
                                <div class="btn btn_base btn-primary build_route main_btn" data-action="pause" :disabled="disable_pause" @click="route_action">Пауза <i
                                        class="far fa-pause-circle"></i></div>
                        </template>
                        <template v-else-if="copter.route.status == '2'">
                            <div v-if="disable_rebuild == false" class="btn btn_base btn-danger build_route main_btn" data-action="rebuild" :disabled="disable_rebuild" @click="route_action">
                                        Перестроить маршрут <i class="fas fa-route"></i></div>
                            <!--<div v-else-if="disable_rebuild == true && disable_rerun == false" class="btn btn_base btn-danger build_route main_btn" data-action="rebuild"  @click="route_action">Отмена <i class="far fa-times-circle"></i></div>-->
                            <div v-if="disable_rebuild == false" class="btn btn_additional btn-primary build_route main_btn" data-action="rerun" :disabled="disable_rerun" @click="route_action">
                                Запустить заного <i class="far fa-play-circle"></i></div>   
                            <div v-if="disable_draw === false && disable_rebuild === true" class="btn btn_base btn-primary build_route main_btn" data-action="draw" @click="route_action">Построить маршрут <i class="fas fa-route"></i></div>
                            <div v-else-if="disable_draw === true && disable_rebuild === true" class="btn btn_base btn-danger build_route main_btn" data-action="draw"  @click="route_action">Отмена <i class="far fa-times-circle"></i></div>
                        </template>
                        <template v-else-if="copter.route.status == '3'">
                            <div class="btn btn_base btn-primary build_route main_btn" data-action="unpause" :disabled="disable_unpause" @click="route_action">
                                            Продолжить <i
                                                class="far fa-play-circle"></i></div>
                        </template>
                        <template v-else-if="copter.route.status == '4'">
                            <div class="btn btn_base btn-danger build_route main_btn" data-action="rebuild" :disabled="disable_rebuild" @click="route_action">
                                            Перестроить маршрут <i class="fas fa-route"></i></div>
                                        <div class="btn btn_additional btn-primary build_route main_btn"
                                             data-action="rerun" :disabled="disable_rerun" @click="route_action">
                                            Запустить заного <i class="far fa-play-circle"></i></div>
                        </template>
                    </template>
                </div>
                <div class="routes_tab_buttons_additional">
                    <div class="btn btn-default btn_slider"
                         @click="toggleCommands()">Команды <i
                            class="fas fa-layer-group"></i></div>
    
                    <div class="btn btn-group" :data-copter-id="copter.id" style="display: none;" ref="btn_group">
                        <div class="btn btn-primary btn_waypoint_add" :disabled="disable_btn_add_waypoint === true" :data-copter-id="copter.id">
                            Добавить точку <br> передвижения <i class="fas fa-map-marker-alt"></i>
                        </div>
                        <div class="btn btn-primary btn_roi_waypoint_add" :disabled="disable_btn_add_roi  === true" :data-copter-id="copter.id">
                            Добавить точку <br> слежения <i class="far fa-eye"></i>
                        </div>
    
                    </div>
                    <div v-if="toggle_roi==false" class="btn btn-primary btn_roi_waypoint" :data-copter-id="copter.id" @click="toggle_roi=!toggle_roi"
                         style="flex-flow: column">
                        Следить за точкой <i class="fas fa-toggle-off"></i> интереса
                    </div>
                    <div v-else class="btn btn-primary btn_roi_waypoint" :data-copter-id="copter.id" @click="toggle_roi=!toggle_roi"
                         style="flex-flow: column">
                        Следить за точкой <i class="fas fa-toggle-on"></i> интереса
                    </div>
                </div>
                <div class="routes_tab_points">

                        <div v-for="point in copter.route.commands" class="point btn btn-default" :data-uid="point.uid"
                             :data-status="point.status"
                             :data-lat="point.coordinates ? point.coordinates[0] : 0"
                             :data-lon="point.coordinates ? point.coordinates[1] : 0">
                            <div class="progress-bar">
                                <span>Прямое движение <i class="fas fa-map-marker-alt"></i></span>
                                <span class="progress-bar-fill"></span>
                            </div>
                        </div>
                </div>
            </div>
    `
});


Vue.component('video-tab', {
    props: {
        copter: Object,
        active_copter: Number,
        cam_url: String,
    },
    data: function () {
        return {
            __copter_id: this.copter.id,
            __name: 'routes-tab',
        }
    },
    methods: {
        getSrcPath : function(){
            return this.copter.camera_color;
        }
    },
    template: `
        <div class="video-tab active" :data-copter-id="copter.id">
            {{this.copter.camera_color}}
            <div class="lightbox">
                <img data-load="true" :id="'player_'+copter.id" :src="''+this.getSrcPath()+''"
                     :data-src="''+getSrcPath()+''" style="width: 100%;"/>
                </img>
            </div>
        </div>
    `
});


window.app = new Vue({
    el: '#main-section',
    data: {
        '__copter_id': 0,
        '__name': 'app',
        'copters': JSParams.copters,
        'bases': JSParams.bases,
        'is_drawing': false,
        'active_copter': 0,
        'player1Activity': false,
        'player4Activity': false,
        'map_preview': false,
        'full_image_height': '0px'
    },
    watch:{
        active_copter: function(val){
            if (val == 1){
                this.player1Activity = true;
                this.player4Activity = false;
            }
            else if(val == 4){
                this.player1Activity = false;
                this.player4Activity = true;
            }
            else{
                this.player1Activity = false;
                this.player4Activity = false;
            }
        },
        map_preview: function(val){
            if (val == true){
                let height = $('.fancybox-content').outerHeight() - 19;
                height = height;
                let full_height = $('.controll-pane').outerHeight();
                full_height = full_height - height - 19;

                $('.controll-pane').animate({
                    height: full_height
                }, 500);
                $('.routes_tab').animate({
                    height: full_height
                }, 500);
                $('.nav-side-menu').animate({
                    height: full_height
                }, 500);
            }
            else{
                $('.controll-pane').animate({
                    height: 100 + '%'
                }, 500);
                $('.routes_tab').animate({
                    height: 100 + '%'
                }, 500);
                $('.nav-side-menu').animate({
                    height: 100 + '%'
                }, 500);
            }
            setTimeout(function(){
                window.Ymap.container.fitToViewport();
            }, 500);
        }
    },
    methods: {
        deleteMapObjectsByType: function (type, copter_id) {
            issetDeletingObjects = true;
            while (issetDeletingObjects == true) {
                issetDeletingObjects = false;
                window.Ymap.geoObjects.each(function (object) {
                    if (object.properties.__type == type && object.properties.__copter_id == copter_id) {
                        window.Ymap.geoObjects.remove(object);
                        issetDeletingObjects = true;
                    }
                })
            }
        }
    },
    mounted: function(){

        var players = $('.video-tab').find('img');
        setInterval(function () {
            for (el_i in app.copters) {
                try{
                    let player = $('.player_' + el_i);



                        let src = $(player).attr('data-src');

                        let result_src = src.substring(0, src.indexOf('mjpg'));
                        result_src = result_src + 'jpg';
                        var img = new Image();
                        try {
                            img.src = result_src;
                            img.onload = function () {
                                if ($(player).attr('data-load') == "false") {
                                    setTimeout(function(){
                                        $(player).attr('src', src);
                                        $(player).attr('data-load', "true");
                                        $(player).css('width', "100%");
                                    }, 5000);

                                } else {
                                    $(player).attr('data-load', "true");
                                }
                            }
                            img.onerror = function () {
                                $(player).attr('data-load', "false");
                                $(player).attr('src', "/media/no_capture.png");
                                $(player).css('width', "50%");
                                $(player).parent().css('text-align', 'center');
                            }
                        } catch (e) {
                            console.log(e);
                        }
                }
                catch (e) {

                }

            }
        }, 5000);

        $(".fancybox").fancybox({
            'opacity': true,
            'overlayShow': true,
            'transitionIn': 'elastic',
            'transitionOut': 'elastic',
            "afterClose": function () {
                $('.fancybox').css('display', 'block');
                app.map_preview = false;
            },
            "beforeShow": function () {
                app.map_preview = true;
            }
        });
    }
    //delimiters: ["[[","]]"]
});

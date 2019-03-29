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
    mounted: function(){
        var item = this.$refs.points_tab;
            Sortable.create(item, {
                animation: 500,
                group: {
                    name: "shared",
                    pull: "clone"
                },
                filter: '[data-status="2"],[data-status="3"],[data-status="4"]',
                sort: true,
                onEnd: function(event){
                    // console.log(event.oldIndex);
                    // console.log(event.newIndex);
                    var keys = Object.keys(app.copters[app.active_copter].route.commands);
                    var commandKeyOld = app.copters[app.active_copter].route.commands[keys[event.oldIndex]].id;
                    var commandKeyNew = app.copters[app.active_copter].route.commands[keys[event.newIndex]].id;
                    var oldItemOrder = app.copters[app.active_copter].route.commands[keys[event.oldIndex]].order;
                    var newItemOrder = app.copters[app.active_copter].route.commands[keys[event.newIndex]].order;

                    $($('.routes_tab_points .point')[event.oldIndex]).insertBefore($($('.routes_tab_points .point')[event.newIndex]));
                    $($('.routes_tab_points .point')[event.newIndex]).insertBefore($($('.routes_tab_points .point')[event.oldIndex]));

                    commands = {};
                    commands[commandKeyOld.toString()] = newItemOrder;
                    commands[commandKeyNew.toString()] = oldItemOrder;
                    wsListener.notSendedMessages[wsListener.notSendedMessages.length] = {
                        type: "change_command_orders",
                        copter_id: app.active_copter,
                        uid: ControlPane.uid(),
                        commands: commands
                    };
                }
            });
    },
    methods: {

        isHandle: function(status){
            if (status != "2" && status != "3" && status != "4"){
                return true;
            }
            else{
                return false;
            }
        },
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
            console.log(action);
            if (action === 'draw') {
                app.is_drawing = !app.is_drawing;

                self.disable_draw = !self.disable_draw;
                if (self.disable_draw === false) {
                    app.deleteMapObjectsByType('route', this.copter.id);
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
                    app.is_drawing = !app.is_drawing;
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
            } else if (action == 'btn_waypoint_add'){
                this.$parent.is_drawing = !this.$parent.is_drawing;
                this.$parent.__drawing_type = "waypoint";
                this.disable_btn_add_waypoint = !this.disable_btn_add_waypoint;
            } else if (action == 'btn_roi_waypoint_add'){
                this.$parent.is_drawing = !this.$parent.is_drawing;
                this.disable_btn_add_roi = !this.disable_btn_add_roi;
                this.$parent.__drawing_type = "roi";
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
                            <div v-if="disable_draw === false" class="btn btn_base btn-primary build_route main_btn" :disabled="disable_btn_add_roi == true || disable_btn_add_waypoint == true" data-action="draw" @click="route_action">Построить маршрут <i class="fas fa-route"></i></div>
                            <div v-else class="btn btn_base btn-danger build_route main_btn" data-action="draw"  @click="route_action">Отмена <i class="far fa-times-circle"></i></div>
                            <!--<div v-else-if="disable_draw === true && copter.route.status == '-1'" class="btn btn_base btn-primary build_route main_btn" data-action="draw" @click="route_action" disabled>Построить маршрут <i class="fas fa-route"></i></div>-->
                    </template>
                    <template v-else>
                        <template v-if="copter.route.status == '-2'">
                                <div v-if="disable_draw === false" class="btn btn_base btn-primary build_route main_btn" :disabled="disable_btn_add_roi == true || disable_btn_add_waypoint == true" data-action="draw" @click="route_action">Построить маршрут <i class="fas fa-route"></i></div>
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
                            <div v-if="disable_rebuild == false" class="btn btn_base btn-danger build_route main_btn" data-action="rebuild" :disabled="disable_rebuild == true || disable_btn_add_roi == true || disable_btn_add_waypoint == true" @click="route_action">
                                        Перестроить маршрут <i class="fas fa-route"></i></div>
                            <!--<div v-else-if="disable_rebuild == true && disable_rerun == false" class="btn btn_base btn-danger build_route main_btn" data-action="rebuild"  @click="route_action">Отмена <i class="far fa-times-circle"></i></div>-->
                            <div v-if="disable_rebuild == false" class="btn btn_additional btn-primary build_route main_btn" data-action="rerun" :disabled="disable_rerun" @click="route_action">
                                Запустить заного <i class="far fa-play-circle"></i></div>   
                            <div v-if="disable_draw === false && disable_rebuild === true" class="btn btn_base btn-primary build_route main_btn" data-action="draw" :disabled="disable_btn_add_roi == true || disable_btn_add_waypoint == true" @click="route_action">Построить маршрут <i class="fas fa-route"></i></div>
                            <div v-else-if="disable_draw === true && disable_rebuild === true" class="btn btn_base btn-danger build_route main_btn" data-action="draw"  @click="route_action">Отмена <i class="far fa-times-circle"></i></div>
                        </template>
                        <template v-else-if="copter.route.status == '3'">
                            <div class="btn btn_base btn-primary build_route main_btn" data-action="unpause" :disabled="disable_unpause" @click="route_action">
                                            Продолжить <i
                                                class="far fa-play-circle"></i></div>
                        </template>
                        <template v-else-if="copter.route.status == '4'">
                            <div class="btn btn_base btn-danger build_route main_btn" data-action="rebuild" :disabled="disable_rebuild || disable_btn_add_roi == true || disable_btn_add_waypoint == true" @click="route_action">
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
                        <div v-if="disable_btn_add_waypoint == false" class="btn btn-primary btn_waypoint_add" data-action="btn_waypoint_add" :disabled="this.$parent.$data.is_drawing === true" :data-copter-id="copter.id" @click="route_action">
                            Добавить точку <br> передвижения <i class="fas fa-map-marker-alt"></i>
                        </div>
                        <div v-else class="btn btn-danger btn_waypoint_add" data-action="btn_waypoint_add" :data-copter-id="copter.id" @click="route_action">
                            Отмена <i class="far fa-times-circle"></i>
                        </div>
                        <div v-if="disable_btn_add_roi == false" class="btn btn-primary btn_roi_waypoint_add" data-action="btn_roi_waypoint_add" :disabled="this.$parent.$data.is_drawing  === true" :data-copter-id="copter.id" @click="route_action">
                            Добавить точку <br> слежения <i class="far fa-eye"></i>
                        </div>
                        <div v-else class="btn btn-danger btn_roi_waypoint_add" data-action="btn_roi_waypoint_add" :data-copter-id="copter.id" @click="route_action">
                            Отмена <i class="far fa-times-circle"></i>
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
                <div class="routes_tab_points" ref="points_tab">
                        
                        <div v-for="(point, key) in copter.route.commands" :key="'route_tab_point_' + key" class="point btn btn-default" :data-uid="point.uid"
                             :data-status="point.status"
                             :data-lat="point.coordinates ? point.coordinates[0] : 0"
                             :data-lon="point.coordinates ? point.coordinates[1] : 0"
                             :data-order="point.order">
                             
                            <div class="progress-bar">
                                <span>Прямое движение <i class="fas fa-map-marker-alt"></i> <i v-if="isHandle(point.status)" class="fas fa-arrows-alt handle"></i></span>
                                <span class="progress-bar-fill"></span>
                            </div>
                        </div>
                </div>
            </div>
    `
});

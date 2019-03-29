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
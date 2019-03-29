// window.busEmitter = new Vue({});
console.log(123123123);
// Подключение компонентов ты
Vue.use('copter-list-item');
Vue.use('copter-bottom-sidebar');
Vue.use('copter-bottom-sidebar-item');
Vue.use('copter-menu');
Vue.use('routes-tab');
Vue.component('notification-item', {
    props: ['typeNotification', 'message'],
    template:
        `
            <div class="notification" :class='[typeNotification]' ref="notification">{{ message }}</div>
        `,
    methods: {
        showNotification: function(){
            var self = this;
            $(self.$refs.notification).stop(true, true).fadeIn().fadeOut(10000);
            setTimeout(function(){
                app.deleteDoneNotification();
            }, 10100);
        }
    },
    mounted: function(){
        this.showNotification();
    }
});
Vue.component('notification', {
    props: ['notifications'],
    template:
    `
        <div class="notification_wrapper">
            <notification-item v-for="(notification, key) in notifications" :typeNotification = "notification.typeNotification" :message = "notification.message"></notification-item>
        </div>
    `,
});

window.app = new Vue({
    el: '#main-section',
    data: {
        '__copter_id': 0,
        '__name': 'app',
        'copters': JSParams.copters,
        'bases': JSParams.bases,
        'is_drawing': false,
        '__drawing_type': '',
        'active_copter': 0,
        'player1Activity': false,
        'player4Activity': false,
        'map_preview': false,
        'full_image_height': '0px',
        'notifications': [],
    },
    watch:{
        active_copter: function(val){ // TODO: ИСПРАВИТЬ !!!!!!!
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
        },
    },
    methods: {
        done_point_build_in_view: function(type, copter_id){
            this.$children.forEach(function(item){
               if (item.$data.__name == 'routes-tab'){
                   if (item.$data.__copter_id == parseInt(copter_id)){
                       item.disable_btn_add_waypoint = false;
                       item.disable_btn_add_roi = false;
                   }
               }
            });
        },
        clearCommands: function(copter_id){
            this.copters[copter_id].route.commands = {};
        },
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
        },
        notification: function(type, message){
            Vue.set(this.notifications, this.notifications.length, {typeNotification:type, message:message});
        },
        deleteDoneNotification: function (index) {
            let i = 0;
            let ind_result;
            for (var ind in this.notifications){
                if (i == 0){
                    ind_result = ind;
                    break
                }
            }
            this.notifications.splice(ind_result, 1);
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


        for (var c_id in this.copters){
            this.$watch(
              function () {
                  return this.copters[c_id].route.commands;
              },
              function (newVal, oldVal) {
                // console.log("................ oldVal ...............");
                // console.log(oldVal);
                // console.log("................ newVal ...............");
                // console.log(newVal);
                // console.log('|||||||||||||||||||||||||||||||||||||||||||||||||');
              }
            )
        }
    }
    //delimiters: ["[[","]]"]
});
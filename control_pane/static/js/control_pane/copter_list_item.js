
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


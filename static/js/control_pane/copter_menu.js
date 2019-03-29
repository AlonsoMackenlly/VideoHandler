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

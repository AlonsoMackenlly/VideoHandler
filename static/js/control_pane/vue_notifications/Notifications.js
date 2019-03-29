var defaults = {
    position: ['top', 'right'],
    cssAnimation: 'vn-fade',
    velocityAnimation: {
        enter: (el) => {
            var height = el.clientHeight;
            return {
                height: [height, 0],
                opacity: [1, 0]
            }
        },
        leave: {
            height: 0,
            opacity: [0, 1]
        }
    }
};
var VelocityGroup = Vue.component('VelocityGroup', {
    name: 'VelocityGroup',
    methods: {
        enter(el, complete) {
            this.$emit('enter', {el, complete})
        },
        leave(el, complete) {
            this.$emit('leave', {el, complete})
        },
        afterLeave() {
            this.$emit('afterLeave')
        }
    },
    template:
        `
        <template>
          <transition-group
            :css="false"
            @enter="enter"
            @leave="leave"
            @after-leave="afterLeave"
          >
            <slot/>
          </transition-group>
        </template>
    `
});


var CssGroup = Vue.component('CssGroup', {
    name: 'CssGroup',
    props: ['name'],
    template: `
        <template>
          <transition-group :name="name">
            <slot/>
          </transition-group>
        </template>
    `
});
const STATE = {
    IDLE: 0,
    DESTROYED: 2
};
Vue.Component('Notifications', {
    name: 'Notifications',
    components: {
        VelocityGroup,
        CssGroup
    },
    props: {
        group: {
            type: String,
            default: ''
        },
        width: {
            type: [Number, String],
            default: 300
        },
        reverse: {
            type: Boolean,
            default: false
        },
        position: {
            type: [String, Array],
            default: () => {
                return defaults.position
            }
        },
        classes: {
            type: String,
            default: 'vue-notification'
        },
        animationType: {
            type: String,
            default: 'css',
            validator(value) {
                return value === 'css' || value === 'velocity'
            }
        },
        animation: {
            type: Object,
            default() {
                return defaults.velocityAnimation
            }
        },
        animationName: {
            type: String,
            default: defaults.cssAnimation
        },
        speed: {
            type: Number,
            default: 300
        },
        /* Todo */
        cooldown: {
            type: Number,
            default: 0
        },
        duration: {
            type: Number,
            default: 3000
        },
        delay: {
            type: Number,
            default: 0
        },
        max: {
            type: Number,
            default: Infinity
        },
        closeOnClick: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            list: [],
            velocity: plugin.params.velocity
        }
    },
    mounted() {
        events.$on('add', this.addItem);
    },
    computed: {
        actualWidth() {
            return parseNumericValue(this.width)
        },
        /**
         * isVelocityAnimation
         */
        isVA() {
            return this.animationType === 'velocity'
        },
        componentName() {
            return this.isVA
                ? 'VelocityGroup'
                : 'CssGroup'
        },
        styles() {
            const {x, y} = listToDirection(this.position)
            const width = this.actualWidth.value
            const suffix = this.actualWidth.type
            let styles = {
                width: width + suffix,
                [y]: '0px'
            }
            if (x === 'center') {
                styles['left'] = `calc(50% - ${width / 2}${suffix})`
            } else {
                styles[x] = '0px'
            }
            return styles
        },
        active() {
            return this.list.filter(v => v.state !== STATE.DESTROYED)
        },
        botToTop() {
            return this.styles.hasOwnProperty('bottom')
        },
    },
    methods: {
        addItem(event) {
            event.group = event.group || ''
            if (this.group !== event.group) {
                return
            }
            if (event.clean || event.clear) {
                this.destroyAll()
                return
            }
            const duration = typeof event.duration === 'number'
                ? event.duration
                : this.duration
            const speed = typeof event.speed === 'number'
                ? event.speed
                : this.speed
            let {title, text, type, data} = event
            const item = {
                id: Id(),
                title,
                text,
                type,
                state: STATE.IDLE,
                speed,
                length: duration + 2 * speed,
                data
            }
            if (duration >= 0) {
                item.timer = setTimeout(() => {
                    this.destroy(item)
                }, item.length)
            }
            let direction = this.reverse
                ? !this.botToTop
                : this.botToTop
            let indexToDestroy = -1
            if (direction) {
                this.list.push(item)
                if (this.active.length > this.max) {
                    indexToDestroy = 0
                }
            } else {
                this.list.unshift(item)
                if (this.active.length > this.max) {
                    indexToDestroy = this.active.length - 1
                }
            }
            if (indexToDestroy !== -1) {
                this.destroy(this.active[indexToDestroy])
            }
        },
        notifyClass(item) {
            return [
                'vue-notification-template',
                this.classes,
                item.type
            ]
        },
        notifyWrapperStyle(item) {
            return this.isVA
                ? null
                : {
                    transition: `all ${item.speed}ms`
                }
        },
        destroy(item) {
            clearTimeout(item.timer)
            item.state = STATE.DESTROYED
            if (!this.isVA) {
                this.clean()
            }
        },
        destroyAll() {
            this.active.forEach(this.destroy)
        },
        getAnimation(index, el) {
            const animation = this.animation[index]
            return typeof animation === 'function'
                ? animation.call(this, el)
                : animation
        },
        enter({el, complete}) {
            const animation = this.getAnimation('enter', el)
            this.velocity(el, animation, {
                duration: this.speed,
                complete
            })
        },
        leave({el, complete}) {
            let animation = this.getAnimation('leave', el)
            this.velocity(el, animation, {
                duration: this.speed,
                complete
            })
        },
        clean() {
            this.list = this.list.filter(v => v.state !== STATE.DESTROYED)
        }
    },
    template:
        `
        <template>
        <div
          class="notifications"
          :style="styles"
        >
          <component
            :is="componentName"
            :name="animationName"
            @enter="enter"
            @leave="leave"
            @after-leave="clean"
          >
            <div
              v-for="item in active"
              class="notification-wrapper"
              :style="notifyWrapperStyle(item)"
              :key="item.id"
              :data-id="item.id"
            >
              <slot
                name="body"
                :class="[classes, item.type]"
                :item="item"
                :close="() => destroy(item)"
              >
                <!-- Default slot template -->
                <div
                  :class="notifyClass(item)"
                  @click="if (closeOnClick) destroy(item)"
                >
                  <div
                    v-if="item.title"
                    class="notification-title"
                    v-html="item.title"
                  >
                  </div>
                  <div
                    class="notification-content"
                    v-html="item.text"
                  >
                  </div>
                </div>
              </slot>
            </div>
          </component>
        </div>
        </template>
    `
});
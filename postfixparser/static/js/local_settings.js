window.addEventListener('load', () => {
    window.LocalSettings = Vue.component('local-settings', {
        template: '#template-settings',
        name: 'local-settings',
        data() {
            return {
                'settings': {
                    'page_limit': 20,
                }
            };
        },
        methods: {
            loadSettings() {
                let s = this.settings;
                if ('page_limit' in window.localStorage)
                    s.page_limit = Number.parseInt(window.localStorage['page_limit']);

                if (isNaN(s.page_limit))
                    s.page_limit = 20;

                this.settings = s;

                this.$emit('settings-loaded', this.settings);
                return s;
            },

            saveSettings() {
                // isNaN is a little stupid, so we double check isNaN() both before and after we try
                // to convert it into an integer. If it's not a number, reset it back to 20.
                if (isNaN(this.settings.page_limit)) { this.settings.page_limit = 20; }
                this.settings.page_limit = Number.parseInt(this.settings.page_limit);
                if (isNaN(this.settings.page_limit)) { this.settings.page_limit = 20; }
                window.localStorage.page_limit = this.settings.page_limit;

                this.$emit('settings-saved', this.settings);
                return this.settings;
            }

        },
        mounted() {
            this.loadSettings();
        }
    });
});


const base_url = '/api/emails';

window.addEventListener('load', () => {
    window.debounce_emails = _.debounce(function () {
        app.loadEmails()
    }, 1000);

    window.app = new Vue({
        el: '#app',
        data: {
            loading: true,
            error: null,
            emails: [],
            search: "",
            search_by: "id",
            status_filter: "NOFILTER",
            page: 1,
            page_count: 1,
            page_reset: false,
            msg: {},
            settings: {
                page_limit: 20
            },
            loaded_settings: false
        },
        computed: {
            email_filter() {
                let d = {};

                if (this.search !== "") {
                    d[this.search_by] = this.search;
                }
                if (this.status_filter !== "NOFILTER") {
                    d['status.code'] = this.status_filter;
                }
                return d;
            },
            has_error() {
                return (
                    (typeof this.error) !== 'undefined' &&
                    this.error !== '' &&
                    this.error !== null &&
                    this.error !== false
                )
            }
        },
        watch: {
            search(val) {
                this.reset_page();
                debounce_emails();
            },
            search_by(val) {
                if (this.search !== "") {
                    this.reset_page();
                    debounce_emails();
                }
            },
            status_filter(val) {
                this.reset_page();
                debounce_emails();
            },
            page(val) {
                if (this.page_reset) return;
                this.loadEmails();
            },
            loaded_settings(newVal, oldVal) {
                if (oldVal === false && newVal === true) {
                    debounce_emails();
                }
            }
        },
        methods: {
            reset_page() {
                this.page_reset = true;
                this.page_count = 1;
                this.page = 1;
                this.page_reset = false;
            },
            loadEmails() {
                this.loading = true;
                var url = base_url, queries = 0;

                for (var f in this.email_filter) {
                    url += (queries === 0) ? '?' : '&';
                    url += `${f}=${this.email_filter[f]}`;
                    queries += 1;
                }

                url += (queries === 0) ? '?' : '&';
                url += `page=${this.page}&limit=${this.settings.page_limit}`;

                return fetch(url).then(function (response) {
                    return response.json();
                }).then((res) => {
                    this.emails = res['result'];
                    this.page_count = res['total_pages'];
                    this.loading = false;
                }).catch((res) => {
                    console.error('Error:', res);
                });
            },
            formatDate(date) {
                let d = new Date(date);
                let newdate = `${d.toLocaleString()}`
            },
            show_modal(m) {
                this.msg = m;
                $('#mail-modal').modal('show');
            },
            settings_saved(val) {
                this.onSettingsUpdated(val);
                notie.alert({type: 'success', text: 'User settings saved successfully :)'})
            },
            settings_loaded(val) {
                this.onSettingsUpdated(val);
                notie.alert({type: 'info', text: `User settings loaded from Local Storage :)`, time: 2})
            },

            onSettingsUpdated(val) {
                let v = JSON.parse(JSON.stringify(val));
                v.page_limit = Number.parseInt(v.page_limit);
                console.log(`[onSettingsUpdated] Old limit: ${this.settings.page_limit} | New Limit: ${v.page_limit}`);
                let updatePage = (v.page_limit !== Number.parseInt(this.settings.page_limit));
                this.settings = v;
                this.loaded_settings = true;
                if (updatePage) {
                    console.log("[onSettingsUpdated] calling debounce_emails");
                    debounce_emails();
                }
                // notie.alert('success', `User settings ${update_type} successfully`)
            }
        },
        mounted() {
            // this.loadEmails();
            // this.debounce_emails = _.debounce(this.loadEmails, 1000);
            $('select.dropdown').dropdown();
        }
    });
});




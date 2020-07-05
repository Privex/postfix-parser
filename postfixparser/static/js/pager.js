window.addEventListener('load', () => {
    window.Pager = Vue.component('pager', {
        template: `
        <div class="ui buttons">
            <button class="ui labeled icon button" :class="{disabled: !has_prev}" @click="$emit('input', page - 1);">
                <i class="left chevron icon"/>Previous Page
            </button>
            <button class="ui button disabled">
                <i class="page icon"/><strong>Page {{ page }} of {{ pageCount }}</strong>
            </button>
            <button class="ui right labeled icon button" :class="{disabled: !has_next}" 
                    @click="$emit('input', page + 1);">
                Next Page <i class="right chevron icon"/>
            </button>
        </div>`,

        props: {
            value: {
                default: 1,
                type: Number
            },
            pageCount: {
                default: 1,
                type: Number
            }
        },
        computed: {
            page() {
                return this.value
            },
            has_next() {
                return this.page < this.pageCount;
            },
            has_prev() {
                return this.page > 1;
            }
        }
    });
});


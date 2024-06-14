import BlockList from './list/List.svelte';

const records = JSON.parse(document.getElementById('record-data').textContent);

const appLang = APP_LANG;

const app = new BlockList({
    target: document.getElementById('block-list'),
    props: {
        blocks: records
    }
});

export default app;

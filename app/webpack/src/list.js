import RecordList from './RecordList.svelte';

const records = JSON.parse(document.getElementById('record-data').textContent);

const appLang = APP_LANG;

const app = new RecordList({
    target: document.getElementById('record-list'),
    props: {
        records: records
    }
});

export default app;

import RecordComponent from './RecordList.svelte';

const records = JSON.parse(document.getElementById('record-data').textContent);

const app = new RecordComponent({
    target: document.getElementById('record-list'),
    props: {
        records: records
    }
});

export default app;

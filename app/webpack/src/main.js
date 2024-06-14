import RecordComponent from './list/List.svelte';

const records = JSON.parse(document.getElementById('record-data').textContent);

const app = new RecordComponent({
    target: document.getElementById('block-list'),
    props: {
        records: records
    }
});

export default app;

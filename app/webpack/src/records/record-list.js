import RecordList from './RecordList.svelte';

const recordApp = new RecordList({
    target: document.getElementById('record-list'),
    props: {
        searchFields
    }
});

export default recordApp;

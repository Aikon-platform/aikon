import RecordList from './RecordList.svelte';
// import { parseData } from "../utils.js";

const recordApp = new RecordList({
    target: document.getElementById('record-list'),
    props: {
        // records: parseData('record-data'),
        searchFields
    }
});

export default recordApp;

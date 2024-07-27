import RecordList from './RecordList.svelte';
// import { parseData } from "../utils.js";

const app = new RecordList({
    target: document.getElementById('record-list'),
    props: {
        // records: parseData('record-data'),
    }
});

export default app;

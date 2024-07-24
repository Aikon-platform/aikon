import RecordList from './RecordList.svelte';
import { parseData } from "../utils.js";

const records = parseData('record-data');

const app = new RecordList({
    target: document.getElementById('record-list'),
    props: {
        records: records,
    }
});

export default app;

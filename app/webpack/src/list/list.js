import BlockList from './List.svelte';
import {parseData} from "../utils.js";


const records = parseData('record-data');
const regions = parseData('regions-data');

// const blocks = records.concat(regions);

const appLang = APP_LANG;

const app = new BlockList({
    target: document.getElementById('block-list'),
    props: {
        // blocks: blocks,
        regions: regions,
        records: records,
    }
});

export default app;

import RecordList from './RecordList.svelte';
import {parseData} from "../utils.js";

const records = parseData('record-data');
const regionsType = "Regions";

const appLang = APP_LANG;

const app = new RecordList({
    target: document.getElementById('record-list'),
    props: {
        records: records,
        regionsType: regionsType,
    }
});

export default app;

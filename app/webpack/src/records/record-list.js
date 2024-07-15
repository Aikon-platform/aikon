import RecordList from './RecordList.svelte';
import {parseData} from "../utils.js";

const records = parseData('record-data');
const regionsType = "Regions";

const app = new RecordList({
    target: document.getElementById('record-list'),
    props: {
        records: records,
        appLang: APP_LANG,
        modules: ADDITIONAL_MODULES,
        regionsType: regionsType,
    }
});

export default app;

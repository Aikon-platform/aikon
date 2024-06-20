import RegionList from './RegionList.svelte';
import {parseData} from "../utils.js";

const regions = parseData('regions-data');
const regionsType = "Regions";
const appLang = APP_LANG;

const app = new RegionList({
    target: document.getElementById('region-list'),
    props: {
        regions: regions,
        regionsType: regionsType,
    }
});

export default app;

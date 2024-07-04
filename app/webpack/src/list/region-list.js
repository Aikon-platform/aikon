import RegionList from './RegionList.svelte';
import {parseData} from "../utils.js";

const regions = parseData('regions-data');
const regionsType = "Regions";

const app = new RegionList({
    target: document.getElementById('region-list'),
    props: {
        regions: regions,
        regionsType: regionsType,
        appLang: APP_LANG,
        modules: ADDITIONAL_MODULES,
        manifest: manifest,
        isValidated: isValidated,
        imgPrefix: imgPrefix,
        nbOfPages: nbOfPages
    }
});
export default app;

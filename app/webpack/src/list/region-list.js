import RegionList from './RegionList.svelte';
import {parseData} from "../utils.js";


const app = new RegionList({
    target: document.getElementById('region-list'),
    props: {
        witness,
        regionsType: "Regions",
        appLang: APP_LANG,
        modules: ADDITIONAL_MODULES,
        manifest,
        isValidated,
        imgPrefix,
        nbOfPages
    }
});
export default app;

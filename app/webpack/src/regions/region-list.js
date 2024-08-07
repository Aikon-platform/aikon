import RegionList from './RegionList.svelte';

const regionApp = new RegionList({
    target: document.getElementById('region-list'),
    props: {
        witness,
        manifest,
        isValidated,
        imgPrefix,
        nbOfPages,
        trailingZeros
    }
});
export default regionApp;

import RegionList from './RegionList.svelte';

const app = new RegionList({
    target: document.getElementById('region-list'),
    props: {
        witness,
        manifest,
        isValidated,
        imgPrefix,
        nbOfPages
    }
});
export default app;

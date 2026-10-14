import RegionView from "./RegionView.svelte";

const RegionApp = new RegionView({
    target: document.getElementById("region-view"),
    props: {
        imgRef,  // eslint-disable-line
    }
});

export default RegionApp;

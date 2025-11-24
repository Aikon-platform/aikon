import WitnessView from "./WitnessView.svelte";

const WitnessApp = new WitnessView({
    target: document.getElementById('witness-view'),
     props: {
        viewTitle,
        editUrl,
        witness,
        manifest,
        manifests,
        isValidated,
        imgPrefix,
        nbOfPages,
        trailingZeros
    }
});

export default WitnessApp;

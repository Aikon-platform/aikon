import WitnessView from "./WitnessView.svelte";

// if we set a default value, then the props defined in the Django template won't be passed to the Svelte instance/
const WitnessApp = new WitnessView({
    target: document.getElementById("witness-view"),
    props: {
        viewTitle,  // eslint-disable-line
        editUrl,  // eslint-disable-line
        witness,  // eslint-disable-line
        manifest,  // eslint-disable-line
        manifests,  // eslint-disable-line
        isValidated,  // eslint-disable-line
        imgPrefix,  // eslint-disable-line
        nbOfPages,  // eslint-disable-line
        trailingZeros  // eslint-disable-line
    }
});

export default WitnessApp;

import WitnessView from "./WitnessView.svelte";

// if we set a default value, then the props defined in the Django template won't be passed to the Svelte instance/
const WitnessApp = new WitnessView({
    target: document.getElementById("witness-view"),
    props: {
        viewTitle,
        editUrl,
        witness,
        isValidated,
    }
});

export default WitnessApp;

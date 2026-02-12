import WitnessView from "./WitnessView.svelte";

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

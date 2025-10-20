import WitnessViewer from "./WitnessViewer.svelte";
import WitnessPanel from "./WitnessPanel.svelte";

const viewer = document.getElementById("witness-viewer");
if (viewer) {
  new WitnessViewer({
    target: viewer,
    props: {
        manifests
    },
  });
}

const panel = new WitnessPanel({
    target: document.getElementById("witness-panel"),
    props: {
      viewTitle,
      witness,
      editUrl,
      manifests,
    },
});

export { panel, viewer };

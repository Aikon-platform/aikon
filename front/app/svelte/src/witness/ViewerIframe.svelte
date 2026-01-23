<script>
    import { onMount } from "svelte";
    import { manifestToMirador } from "../utils.js";

    let iframeSrc = "";

    onMount(() => {
      if (manifests.length > 0) iframeSrc = manifestToMirador(manifests[0]);

      function handler(e) {
        iframeSrc = manifestToMirador(e.detail.selectedManifest);
      }

      window.addEventListener("selectManifest", handler);
    });
</script>

<iframe
    src={iframeSrc}
    style="width: 100%; height: 75vh; border: none;"
    title="Mirador viewer"
    allowfullscreen
></iframe>

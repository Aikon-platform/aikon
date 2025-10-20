<script>
  import { onMount } from "svelte";
  import { manifestToMirador } from "../utils.js";
  import { appLang } from "../constants";

  export let manifests = [];

  let iframeSrc = "";

  function updateViewer(manifest) {
    iframeSrc = manifestToMirador(manifest);
  }

  onMount(() => {
    if (manifests.length > 0) {
      iframeSrc = manifestToMirador(manifests[0]);
    }
    window.addEventListener("manifestChange", (e) => {
      updateViewer(e.detail.manifest);
    });
  });
</script>

<div style="height: 80vh">
  {#if iframeSrc}
    <iframe
      src={iframeSrc}
      style="width: 100%; height: 100%; border: none;"
      title="Mirador viewer"
      allowfullscreen
    ></iframe>
  {:else}
    <div class="has-text-centered p-6">
      <progress class="progress is-small is-primary" max="100">
        {appLang === 'en' ? 'Loading...' : "Chargement..."}
      </progress>
      <p>
        {appLang === 'en'
          ? 'Loading witness digitization...'
          : "Chargement de la numérisation..."}
      </p>
    </div>
  {/if}
</div>

<script>
  export let viewTitle = "";
  export let witness = {};
  export let editUrl = "";
  export let manifests = [];

  let currentManifest = manifests?.[0] || "";

  function handleManifestChange(e) {
  currentManifest = e.target.value;

  const event = new CustomEvent("manifestChange", {
    detail: {
      manifest: currentManifest
    },
  });
  window.dispatchEvent(event);
}
</script>

<style>
.panel {
  height: 80vh;
  overflow-y: auto;
}
.witness-key {
  display: block;
  font-weight: bold;
  border-bottom: 1px solid var(--bulma-border);
  padding: 10px 0;
}
.selector {
  margin-bottom: 1rem;
}
</style>

<div class="panel box">
  <h2 class="title is-4 mb-4">
    {viewTitle}
    <a
      href={editUrl}
      class="edit-btn button is-small is-rounded is-link px-3 ml-3 mt-3"
      title="Edit"
    >
      <span class="iconify" data-icon="entypo:edit"></span>
    </a>
  </h2>

  {#if manifests.length > 0}
    <div class="field selector">
      <label for="digit" class="label">Digitization</label>
      <div id="digit" class="control">
        <div class="select is-small">
          <select bind:value={currentManifest} on:change={handleManifestChange}>
            {#each manifests as m}
              <option value={m}>
                {m.match(/\/([^\/]+)\/manifest\.json$/)?.[1] || m}
              </option>
            {/each}
          </select>
        </div>
      </div>
    </div>
  {/if}

  <div class="content">
    {#each Object.entries(witness.metadata_full.wit) as [key, value]}
      <span class="witness-key">{key}</span><br />
      <span class="witness-value">{value}</span>
    {/each}

    {#if witness.metadata_full.contents?.length}
      <h3 class="title is-5 mb-3">Contents</h3>
      {#each witness.metadata_full.contents as content}
        <div class="mb-3">
          <span class="witness-key">{content.title}</span>
          {#if content.content}
            {#each Object.entries(content.content) as [key, value]}
              <div class="witness-value"><b>{key}:</b> {value}</div>
            {/each}
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>

<script>
    import {appLang, modules} from "../constants.js";

    export let viewTitle = "";
    export let witness = {};
    export let editUrl = "";
    export let manifests = [];

    const layouts = {
        viewer: { text: appLang === 'en' ? 'Viewer' : 'Visionneuse' },
        all: { text: appLang === 'en' ? 'All regions' : 'Toutes les régions' },
        page: { text: appLang === 'en' ? 'Per page' : 'Par page' },
    }
    if (modules.includes("similarity")) layouts.similarity = { text: appLang === 'en' ? 'Similarity' : 'Similarité' }
    if (modules.includes("vectorization")) layouts.vectorization = { text: appLang === 'en' ? 'Vectorization' : 'Vectorisation' }

    $: currentLayout = new URLSearchParams(window.location.search).get("tab") ?? "viewer";

    function changeLayout(layout) {
        currentLayout = layout;
        const url = new URL(window.location);
        url.searchParams.set("tab", layout);
        window.history.pushState({}, "", url);
    }

    let manifest = manifests?.[0] || "";

    function selectManifest(e) {
        manifest = e.target.value;
        const event = new CustomEvent("selectManifest", {
            detail: {
                manifest: manifest
            },
        });
        window.dispatchEvent(event);
    }
</script>

<div class="panel box">
    <div class="content">
        <h2 class="title is-4 mb-4">
            {viewTitle}
            <a
                href={editUrl}
                class="edit-btn button is-small is-rounded is-link px-4 ml-3 mt-3"
                title="Edit"
            >
                <span class="iconify" data-icon="entypo:edit"></span>
            </a>
        </h2>

        {#if manifests.length > 0}
            <div class="field selector">
                <label for="digit" class="label">
                    {appLang === 'en' ? "Digitization" : 'Numérisation'}
                </label>
                <div id="digit" class="control">
                    <div class="select is-small">
                        <select bind:value={manifest} on:change={selectManifest}>
                            {#each manifests as manifest}
                                <option value={manifest}>
                                    {manifest}
                                </option>
                            {/each}
                        </select>
                    </div>
                </div>
            </div>
        {/if}

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
</style>

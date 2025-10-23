<script>
    import { onMount } from "svelte";
    import { manifestToMirador } from "../utils.js";
    import { appLang } from "../constants";

    export let manifests = [];

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

    let iframeSrc = "";

    onMount(() => {
        if (manifests.length > 0) {
            iframeSrc = manifestToMirador(manifests[0]);
        }
        window.addEventListener("selectManifest", (e) => {
            iframeSrc = manifestToMirador(e.detail.manifest);
        });
    });
</script>

{#if manifests.length > 0}
    <div class="field selector is-flex">
        <label for="digit" class="label">
            {appLang === 'en' ? "Digitization" : 'Numérisation'}
        </label>
        <div id="digit" class="control pl-3">
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

<iframe
    src={iframeSrc}
    style="width: 100%; height: 90%; border: none;"
    title="Mirador viewer"
    allowfullscreen
></iframe>

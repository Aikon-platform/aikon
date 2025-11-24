<script>
    import {appLang} from "../constants.js";

    export let manifests;

    let selectedManifest = manifests?.[0] || "";

    function selectManifest(e) {
        selectedManifest = e.target.value;
        window.dispatchEvent(new CustomEvent("selectManifest", {
            detail: { selectedManifest }
        }));
    }
</script>

<div class="field selector is-flex is-right mb-2">
    <label for="digit" class="label">
        {appLang === 'en' ? "Digitization" : 'Numérisation'}
    </label>
    <div id="digit" class="control pl-3">
        <div class="select is-small">
            <select bind:value={selectedManifest} on:change={selectManifest}>
                {#each manifests as man}
                    <option value={man}>
                        {man}
                    </option>
                {/each}
            </select>
        </div>
    </div>
</div>

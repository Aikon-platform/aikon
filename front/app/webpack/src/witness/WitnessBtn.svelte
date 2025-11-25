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

    function manifestLabel(url) {
        const manifestId = url.match(/man(\d+)/)[1];
        const regionsExtId = url.match(/anno(\d+)/);
        const regionsExtNumber = regionsExtId ? regionsExtId[1] : null;

        let label = "";
        label += `${appLang === "en" ? "Manifest" : "Manifeste"} #${manifestId}`;

        if (regionsExtNumber) {
            label += `, ${appLang === "en" ? "Regions extraction" : "Extraction de régions"} #${regionsExtNumber}`;
        }

        return label;
    }
</script>

<div class="field selector is-flex is-right mb-2">
    <label for="digit" class="label">
        {appLang === 'en' ? "Digitization:" : 'Numérisation :'}
    </label>
    <div id="digit" class="control pl-3">
        <div class="select is-small">
            <select bind:value={selectedManifest} on:change={selectManifest}>
                {#each manifests as man}
                    <option value={man}>
                        {manifestLabel(man)}
                    </option>
                {/each}
            </select>
        </div>
    </div>
</div>

<script>
    import {i18n, manifestToMirador} from "../utils.js";
    import {appLang} from "../constants.js";

    export let witnessStore;
    const { manifests, selectedManifest } = witnessStore;

    $: iframeSrc = manifestToMirador($selectedManifest);

    function manifestLabel(url) {
        const manifest = url.match(/(?:man|img|pdf)(\d+)/);
        const manifestId = manifest?.[1] ?? "?";
        return `${i18n("Manifest")} #${manifestId}`;
    }
</script>

<div class="field selector is-flex is-right mb-2">
    <label for="digit" class="label mt-1">
        {i18n('Digitization')}
    </label>
    <div id="digit" class="control pl-3">
        <div class="select is-small">
            <select on:change={(event) => witnessStore.selectedManifest(event.target.value)}>
                {#each $manifests as man}
                    <option value={man}>{manifestLabel(man)}</option>
                {/each}
            </select>
        </div>
    </div>
</div>

<iframe src={iframeSrc} style="width: 100%; height: 75vh; border: none;" title="Mirador viewer" allowfullscreen/>

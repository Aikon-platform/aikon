<script>
    import {refToIIIF} from "../utils.svelte.js";
    import {appLang} from "../constants.js";
    import SelectionModal from "../selection/SelectionModal.svelte";
    import SelectionBtn from "../selection/SelectionBtn.svelte";

    let { selectionStore } = $props();
    const { selected } = selectionStore;

    // $selected = {"Regions"/"Cluster" : {id: {S}, id: {E}, id: {L}, id: {E}, id: {C}, id: {T}}}
    let selectedRegions = $derived(Object.values($selected)[0] || {});
    let selectionLength = $derived(Object.keys(selectedRegions).length);
    let areSelectedRegions = $derived(selectionLength > 0);
</script>

<SelectionBtn {selectionLength}/>

<SelectionModal {selectionLength} {selectionStore}>
    {#if areSelectedRegions}
        <div class="fixed-grid has-6-cols">
            <div class="grid is-gap-2">
                {#each Object.entries(selectedRegions) as [id, meta]}
                    <div class="selection cell">
                        <figure class="image is-64x64 card">
                            <img src="{refToIIIF(meta.img, meta.xywh, '96,')}" alt="Extracted region"/>
                            <div class="overlay is-center">
                                <span class="overlay-desc">{meta.title}</span>
                            </div>
                        </figure>
                        <button class="delete region-btn" aria-label="remove from selection"
                                onclick={() => selectionStore.remove(id, Object.keys($selected)[0])}></button>
                    </div>
                {/each}
            </div>
        </div>
    {:else}
        <div>
            {appLang === "en" ? "No regions in selection" : "Aucune région sélectionnée"}
        </div>
    {/if}
</SelectionModal>

<style>
    .selection {
        position: relative;
        width: 64px;
    }
    .selection .delete {
        position: absolute;
        top: -0.75rem;
        right: -0.75rem;
    }
    .overlay {
        font-size: 50%;
    }
</style>

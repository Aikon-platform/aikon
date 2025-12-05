<script>
    import {refToIIIF} from "../utils.js";
    import {appLang, regionsType} from "../constants.js";
    import SelectionModal from "../selection/SelectionModal.svelte";
    import SelectionBtn from "../selection/SelectionBtn.svelte";

    export let selectionStore = regionsSelection;
    const { selected } = selectionStore;

    // $selected = {"Regions"/"Cluster" : [{S}, {E}, {L}, {E}, {C}, {T}, {I}, {O}, {N}]}
    $: selectedRegions = Object.values($selected)[0] || {};
    $: selectionLength = Object.keys(selectedRegions).length;
    $: areSelectedRegions = selectionLength > 0;
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
                                on:click={() => selectionStore.remove(id, regionsType)}/>
                    </div>
                {/each}
            </div>
        </div>
    {:else}
        <div>
            {appLang === 'en' ? 'No regions in selection' : 'Aucune région sélectionnée'}
        </div>
    {/if}
</SelectionModal>

<style>
    .selection {
        position: relative;
        width: 64px;
    }
    .overlay {
        font-size: 50%;
    }
</style>

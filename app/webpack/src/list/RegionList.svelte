<script>
    import {refToIIIF} from "../utils.js";
    import { selectionStore } from './stores/selectionStore.js';
    const { selected } = selectionStore;
    import { regionsStore } from './stores/regions.js';
    const { allRegions, fetchAll, pageRegions, fetchPages } = regionsStore;
    import { loading } from '../utils.js';
    import Loading from '../Loading.svelte';

    import Region from './Region.svelte';
    import SelectionBtn from "./SelectionBtn.svelte";
    import SelectionFooter from "./SelectionFooter.svelte";
    import RegionsRow from "./RegionsRow.svelte";
    import Pagination from "./Pagination.svelte";
    import Modal from "../Modal.svelte";
    import ExtractionButtons from "./ExtractionButtons.svelte";
    import RegionsBtn from "./RegionsBtn.svelte";
    import ActionButtons from "./ActionButtons.svelte";

    export const regionsType = "Regions"
    // export let regions = {};
    export let appLang = 'en';
    export let manifest = '';
    export let isValidated = false;
    export let imgPrefix = '';
    export let nbOfPages = 1;
    export let modules = [];
    export let witness = {};
    const zeros = (n, l) => n.toString().padStart(l, '0');

    $: selectedRegions = $selected(true);
    $: selectionLength = Object.keys(selectedRegions).length;
    $: areSelectedRegions = selectionLength > 0;

    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentRegionId = parseInt(baseUrl.split('regions/')[1].replace("/", ""));


    function toImgName(canvasNb){
        return `${imgPrefix}_${zeros(canvasNb, String(nbOfPages).length + 1)}`;
    }

    const layouts = {
        all: { text: appLang === 'en' ? 'All regions' : 'Toutes les régions' },
        page: { text: appLang === 'en' ? 'Per page' : 'Par page' },
    }
    if (modules.includes("similarity")) layouts.similarity = { text: appLang === 'en' ? 'Similarity' : 'Similarité' }
    if (modules.includes("vectorization")) layouts.vectorization = { text: appLang === 'en' ? 'Vectorization' : 'Vectorisation' }

    $: currentLayout = "all"

    $: clipBoard = "";
    // NOTE: isItemCopied stays to true if user copied another string
    $: isItemCopied = (item) => clipBoard === item.ref;
    function handleCopyRef(event) {
        const { item } = event.detail;
        const itemRef = isItemCopied(item) ? "" : item.ref;
        navigator.clipboard.writeText(itemRef);
        clipBoard = itemRef;
    }
</script>

<Loading visible={$loading}/>

<Modal {appLang}/>

<SelectionBtn {selectionLength} {appLang} />

<div id="nav-actions" class="mb-5">
    <div class="actions grid">
        <div class="cell is-right is-middle">
            <RegionsBtn {appLang} {witness} {baseUrl} {currentRegionId}/>
        </div>
        <div class="cell">
            <ActionButtons {appLang} {manifest} {isValidated} {regionsType}/>
        </div>
    </div>

    <div class="tabs is-centered">
        <ul class="panel-tabs">
            {#each Object.entries(layouts) as [layout, meta]}
                <!--TODO make active tab appear in url-->
                <li class:is-active={layout === currentLayout}
                    on:click={() => currentLayout = layout} on:keyup={() => null}>
                    <a href={null}>{meta.text}</a>
                </li>
            {/each}
        </ul>
    </div>
</div>


{#if currentLayout === "all"}
    <div class="grid is-gap-2">
        {#await fetchAll}
            <tr class="faded is-center">
                {appLang === 'en' ? 'Retrieving regions...' : 'Récupération des régions...'}
            </tr>
        {:then _}
            {#each Object.values($allRegions) as item (item.id)}
                <!--TODO dont sort object keys alphabetically-->
                <Region {item} {appLang}
                        isCopied={isItemCopied(item)}
                        on:copyRef={handleCopyRef}/>
            {:else}
                <ExtractionButtons {appLang} {modules} {witness} {currentRegionId} {baseUrl}/>
            {/each}
        {:catch error}
            <tr>Error when retrieving regions: {error}</tr>
        {/await}
    </div>
{:else if currentLayout === "page"}
    <Pagination {nbOfPages}/>

    <table class="table is-fullwidth">
        <tbody>

        {#await $fetchPages}
            <tr class="faded is-center">
                {appLang === 'en' ? 'Retrieving paginated regions...' : 'Récupération des pages...'}
            </tr>
        {:then _}
            {#if Object.values($pageRegions).length > 0}
                <!--TODO make empty canvases appear-->
                {#each Object.entries($pageRegions) as [canvasNb, items]}
                    <RegionsRow canvasImg={toImgName(canvasNb)} {canvasNb} {manifest}>
                        {#each Object.values(items) as item (item.id)}
                            <Region {item} {appLang} isSquare={false}
                                    isCopied={isItemCopied(item)}
                                    on:copyRef={handleCopyRef}/>
                        {/each}
                    </RegionsRow>
                {/each}
            {:else}
                <tr>
                    <ExtractionButtons {appLang} {modules} {witness}/>
                </tr>
            {/if}
        {:catch error}
            <tr>Error when retrieving paginated regions: {error}</tr>
        {/await}

        </tbody>
    </table>
{:else if currentLayout === "similarity"}
    <div>tout doux</div>
{:else if currentLayout === "vectorization"}
    <div>tout doux</div>
{/if}

<!--TODO create component with slot for items-->
<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"/>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <i class="fa-solid fa-book-bookmark"></i>
                {appLang === 'en' ? 'Selected regions' : 'Regions sélectionnées'}
                ({selectionLength})
            </div>
            <button class="delete media-left" aria-label="close"/>
        </div>
        <section class="modal-card-body">
            {#if areSelectedRegions}
                <div class="fixed-grid has-6-cols">
                    <div class="grid is-gap-2">
                        {#each Object.entries(selectedRegions) as [id, meta]}
                            <div class="selection cell">
                                <figure class="image is-64x64 card">
                                    <img src="{refToIIIF(meta.img, meta.xyhw, '96,')}" alt="Extracted region"/>
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
        </section>
        <SelectionFooter {appLang} isRegion={true}/>
    </div>
</div>

<style>
    .selection {
        position: relative;
        width: 64px;
    }
    .overlay {
        font-size: 50%;
    }
    /*.actions {*/
    /*    align-items: flex-end;*/
    /*}*/
    #nav-actions {
        position: sticky;
        top: 0;
        z-index: 2;
        background-color: var(--bulma-body-background-color);
        box-shadow: var(--bulma-body-background-color) 0 0 25px;
        padding-top: 5em;
        margin-top: -5em;
    }
</style>

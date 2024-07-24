<script>
    import { setContext } from 'svelte';
    import { fade } from 'svelte/transition';
    import { refToIIIF } from "../utils.js";
    import { selectionStore } from '../selection/selectionStore.js';
    const { selected } = selectionStore;
    import { regionsStore } from './regionsStore.js';
    const { allRegions, fetchAll } = regionsStore;
    import { loading } from '../utils.js';
    import { appLang, regionsType, modules } from '../constants';
    import Loading from '../Loading.svelte';
    import Region from './Region.svelte';
    import SelectionBtn from "../selection/SelectionBtn.svelte";
    import Modal from "../Modal.svelte";
    import ExtractionButtons from "./ExtractionButtons.svelte";
    import RegionsBtn from "./RegionsBtn.svelte";
    import ActionButtons from "./ActionButtons.svelte";
    import Similarity from "./similarity/Similarity.svelte";
    import PageRegions from "./PageRegions.svelte";
    import SelectionModal from "../selection/SelectionModal.svelte";

    export let manifest = '';
    export let isValidated = false;
    export let imgPrefix = '';
    export let nbOfPages = 1;
    export let witness = {};

    setContext('witness', witness);
    setContext('nbOfPages', nbOfPages);
    setContext('imgPrefix', imgPrefix);
    setContext('manifest', manifest);
    setContext('isValidated', isValidated);

    $: selectedRegions = $selected(true);
    $: selectionLength = Object.keys(selectedRegions).length;
    $: areSelectedRegions = selectionLength > 0;

    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentRegionId = parseInt(baseUrl.split('regions/')[1].replace("/", ""));

    const layouts = {
        all: { text: appLang === 'en' ? 'All regions' : 'Toutes les régions' },
        page: { text: appLang === 'en' ? 'Per page' : 'Par page' },
    }
    if (modules.includes("similarity")) layouts.similarity = { text: appLang === 'en' ? 'Similarity' : 'Similarité' }
    if (modules.includes("vectorization")) layouts.vectorization = { text: appLang === 'en' ? 'Vectorization' : 'Vectorisation' }

    $: currentLayout = new URLSearchParams(window.location.search).get("tab") ?? "all";

    function changeLayout(layout) {
        currentLayout = layout;
        const url = new URL(window.location);
        url.searchParams.set("tab", layout);
        window.history.pushState({}, "", url);
    }
</script>

<Loading visible={$loading}/>

<Modal/>

<SelectionBtn {selectionLength}/>

<div id="nav-actions" class="mb-5">
    <div class="actions grid">
        <div class="cell is-right is-middle">
            <RegionsBtn {baseUrl} {currentRegionId}/>
        </div>
        {#if ["all", "page"].includes(currentLayout)}
            <div class="cell" transition:fade={{ duration: 500 }}>
                <ActionButtons/>
            </div>
        {/if}
    </div>

    <div class="tabs is-centered">
        <ul class="panel-tabs">
            {#each Object.entries(layouts) as [layout, meta]}
                <li class:is-active={layout === currentLayout}
                    on:click={() => changeLayout(layout)} on:keyup={() => null}>
                    <a href={null}>{meta.text}</a>
                </li>
            {/each}
        </ul>
    </div>
</div>


{#if currentLayout === "all"}
    <div class="grid is-gap-2">
        {#await fetchAll}
            <div class="faded is-center">
                {appLang === 'en' ? 'Retrieving regions...' : 'Récupération des régions...'}
            </div>
        {:then _}
            {#each Object.values($allRegions) as item (item.id)}
                <Region {item}/>
            {:else}
                <ExtractionButtons {currentRegionId} {baseUrl}/>
            {/each}
        {:catch error}
            <div>Error when retrieving regions: {error}</div>
        {/await}
    </div>
{:else if currentLayout === "page"}
    <PageRegions/>
{:else if currentLayout === "similarity"}
    <Similarity/>
{:else if currentLayout === "vectorization"}
    <div>tout doux</div>
{/if}

<SelectionModal isRegion={true} {selectionLength}>
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
</SelectionModal>

<style>
    .selection {
        position: relative;
        width: 64px;
    }
    .overlay {
        font-size: 50%;
    }
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

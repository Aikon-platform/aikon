<script>
    import { setContext } from 'svelte';
    import { fade } from 'svelte/transition';
    import { loading } from "../utils.js";
    import { appLang, modules } from '../constants';

    import { regionsSelection } from "../selection/selectionStore.js";
    import { regionsStore } from './regionsStore.js';
    const { allRegions, fetchAll } = regionsStore;

    import Loading from '../Loading.svelte';
    import Modal from "../Modal.svelte";
    import ExtractionButtons from "./ExtractionButtons.svelte";
    import RegionsBtn from "./RegionsBtn.svelte";
    import ActionButtons from "./ActionButtons.svelte";
    import Similarity from "./similarity/Similarity.svelte";
    import PageRegions from "./PageRegions.svelte";
    import Vectorization from "./vectorization/Vectorization.svelte";
    import RegionsSelectionModal from "./RegionsSelectionModal.svelte";
    import Regions from "./Regions.svelte";

    export let manifest = '';
    export let isValidated = false;
    export let imgPrefix = '';
    export let nbOfPages = 1;
    export let trailingZeros = 1;
    export let witness = {};

    setContext('witness', witness);
    setContext('nbOfPages', nbOfPages);
    setContext('trailingZeros', trailingZeros);
    setContext('imgPrefix', imgPrefix);
    setContext('manifest', manifest);
    setContext('isValidated', isValidated);

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

<Loading/>

<Modal/>

<RegionsSelectionModal selectionStore={regionsSelection}/>

<div id="nav-actions">
    <div class="actions grid">
        <div class="cell is-left is-middle">
            <RegionsBtn {baseUrl} {currentRegionId} {currentLayout}/>
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
    <div class="grid is-gap-2 mt-5">
        {#await fetchAll}
            <div class="faded is-center">
                {appLang === 'en' ? 'Retrieving regions...' : 'Récupération des régions...'}
            </div>
        {:then _}
            {#if Object.values($allRegions).length}
                <Regions items={Object.values($allRegions)} selectionStore={regionsSelection}/>
            {:else}
                <ExtractionButtons {currentRegionId} {baseUrl}/>
            {/if}
        {:catch error}
            <div>Error when retrieving regions: {error}</div>
        {/await}
    </div>
{:else if currentLayout === "page"}
    <PageRegions/>
{:else if currentLayout === "similarity"}
    <Similarity/>
{:else if currentLayout === "vectorization"}
    <Vectorization/>
{/if}

<style>
    #nav-actions {
        position: sticky;
        top: 0;
        z-index: 2;
        background-color: var(--bulma-body-background-color);
        box-shadow: var(--bulma-body-background-color) 0 0 25px;
        padding-top: 5em;
        margin-top: -5em;
    }
    #nav-actions .panel-tabs {
        margin-inline-start: 0;
        margin-top: 0;
    }
</style>

<script>
    import { setContext } from "svelte";
    import { fade } from 'svelte/transition';
    import { refToIIIF, loading } from "../utils.js";
    import { appLang, regionsType, modules } from "../constants";

    import { regionsSelection } from "../selection/selectionStore.js";
    const { selected, nbSelected, remove } = regionsSelection;
    import { regionsStore } from "../regions/regionsStore.js";
    const { allRegions, fetchAll } = regionsStore;

    import Layout from "../Layout.svelte";
    import WitnessPanel from "../witness/WitnessPanel.svelte"
    import Loading from "../Loading.svelte";
    import SelectionBtn from "../selection/SelectionBtn.svelte";
    import Modal from "../Modal.svelte";
    import ExtractionButtons from "../regions/ExtractionButtons.svelte";
    import ActionButtons from "../regions/ActionButtons.svelte";
    import Similarity from "../regions/similarity/Similarity.svelte";
    import PageRegions from "../regions/PageRegions.svelte";
    import SelectionModal from "../selection/SelectionModal.svelte";
    import Vectorization from "../regions/vectorization/Vectorization.svelte";
    import Viewer from "../witness/ViewerIframe.svelte";
    import WitnessBtn from "../witness/WitnessBtn.svelte";
    import ExportButtons from "../regions/vectorization/ExportButtons.svelte";
    import Regions from "../regions/Regions.svelte";
    import { activeLayout } from '../ui/tabStore.js';

    export let manifest = "";
    export let manifests = [];
    export let isValidated = false;
    export let imgPrefix = "";
    export let nbOfPages = 1;
    export let trailingZeros = 1;
    export let witness = {};
    export let editUrl = "";
    export let viewTitle = "";

    setContext("witness", witness);
    setContext("nbOfPages", nbOfPages);
    setContext("trailingZeros", trailingZeros);
    setContext("imgPrefix", imgPrefix);
    setContext("manifest", manifest);
    setContext("isValidated", isValidated);

    $: selectedRegions = $selected;
    $: selectionLength = $nbSelected;
    $: areSelectedRegions = selectionLength > 0;

    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentRegionId = parseInt(baseUrl.split("regions/")[1].replace("/", ""));

    const tabList = {
        viewer: appLang === "en" ? "Viewer" : "Visionneuse",
        all: appLang === "en" ? "All regions" : "Toutes les régions",
        page: appLang === "en" ? "Per page" : "Par page",
    };

    if (modules.includes("similarity")) {
        tabList.similarity = appLang === "en" ? "Similarity" : "Similarité";
    }
    if (modules.includes("vectorization")) {
        tabList.vectorization = appLang === "en" ? "Vectorization" : "Vectorisation";
    }
</script>

<Loading visible={$loading}/>

<Modal/>

<SelectionBtn {selectionLength}/>

<Layout {tabList}>
    <div slot="sidebar">
        <WitnessPanel {witness} {editUrl} {viewTitle}/>
    </div>

    <div slot="content">
        {#if manifests.length === 0}
            <article class="message is-warning">
                <div class="message-body">
                    {appLang === "en" ? "This witness has no digitization." : "Ce témoin n'a pas de numérisation."}
                </div>
            </article>
        {:else}
            <div id="nav-actions">
                <div class="actions grid">
                    <div class="cell">
                        {#if $activeLayout === "all" || $activeLayout === "page" }
                            <ActionButtons/>
                        {:else if $activeLayout === "viewer"}
                            <WitnessBtn {manifests}/>
                        {:else if $activeLayout === "vectorization"}
                            <ExportButtons/>
                        {/if}
                    </div>
                </div>
            </div>

            {#if $activeLayout === "viewer"}
                <Viewer/>

            {:else if $activeLayout === "all"}
                <div class="grid is-gap-2 mt-5">
                    {#await fetchAll}
                        <div class="faded is-center">
                            {appLang === "en" ? "Retrieving regions..." : "Récupération des régions..."}
                        </div>
                    {:then _}
                        {#if Object.values($allRegions).length}
                            <Regions items={Object.values($allRegions)}/>
                        {:else}
                            <ExtractionButtons {currentRegionId} {baseUrl}/>
                        {/if}
                    {:catch error}
                        <div>Error when retrieving regions: {error}</div>
                    {/await}
                </div>

            {:else if $activeLayout === "page"}
                <PageRegions/>

            {:else if $activeLayout === "similarity"}
                <Similarity/>

            {:else if $activeLayout === "vectorization"}
                <Vectorization/>
            {/if}
        {/if}
    </div>
</Layout>

<SelectionModal {selectionLength} selectionStore={regionsSelection}>
    {#if areSelectedRegions}
        <div class="fixed-grid has-6-cols">
            <div class="grid is-gap-2">
                {#each Object.entries(selectedRegions) as [type, selectedItems]}
                    {#each Object.entries(selectedItems) as [id, meta]}
                        <div class="selection cell">
                            <figure class="image is-64x64 card">
                                <img src="{refToIIIF(meta.img, meta.xywh, '96,')}" alt=""/>
                                <div class="overlay is-center">
                                    <span class="overlay-desc">{meta.title}</span>
                                </div>
                            </figure>
                            <button class="delete region-btn"
                                on:click={() => remove(id, regionsType)}/>
                        </div>
                    {/each}
                {/each}
            </div>
        </div>
    {:else}
        <div>{appLang === "en" ? "No regions in selection" : "Aucune région sélectionnée"}</div>
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

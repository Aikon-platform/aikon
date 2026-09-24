<script>
    import { setContext } from "svelte";
    import { refToIIIF, loading } from "../utils.js";
    import { appLang, regionsType, modules } from "../constants";

    import { createWitnessStore } from "./witnessStore.js";
    import { regionsSelection } from "../selection/selectionStore.js";
    const { nbSelected: nbRegionSelected } = regionsSelection;
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
    import Vectorization from "../regions/vectorization/Vectorization.svelte";
    import Viewer from "../witness/ViewerIframe.svelte";
    import ExportButtons from "../regions/vectorization/ExportButtons.svelte";
    import Regions from "../regions/Regions.svelte";
    import { activeLayout } from "../ui/tabStore.js";
    import RegionsSelectionModal from "../regions/RegionsSelectionModal.svelte";

    export let isValidated = false;
    export let witness = {};
    export let editUrl = "";
    export let viewTitle = "";

    const witnessStore = createWitnessStore(witness.digits);

    setContext("witness", witness);
    setContext("isValidated", isValidated);

    $: regionSelectionLength = $nbRegionSelected;

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

<div class="set-container">
    <SelectionBtn {regionSelectionLength} selectionType="region-set"/>
</div>

<Layout {tabList}>
    <div slot="sidebar">
        <WitnessPanel {witness} {editUrl} {viewTitle}/>
    </div>

    <div slot="content">
        {#if !witnessStore.hasDigit()}
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
                            <ActionButtons {witnessStore}/>
                        {:else if $activeLayout === "vectorization"}
                            <ExportButtons/>
                        {/if}
                    </div>
                </div>
            </div>

            {#if $activeLayout === "viewer"}
                <Viewer {witnessStore}/>

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
                <PageRegions {witnessStore}/>

            {:else if $activeLayout === "similarity"}
                <Similarity {witnessStore}/>

            {:else if $activeLayout === "vectorization"}
                <Vectorization/>
            {/if}
        {/if}
    </div>
</Layout>

<RegionsSelectionModal selectionLength={regionSelectionLength} selectionStore={regionsSelection} selectionType="region-set"/>

<style>
    .set-container {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        position: fixed;
        bottom: 0;
        right: 0;
        z-index: 10;
    }
</style>

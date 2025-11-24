<script>
    import { setContext } from "svelte";
    import { fade } from 'svelte/transition';
    import { refToIIIF, loading } from "../utils.js";
    import { appLang, regionsType, modules } from "../constants";

    import { selectionStore } from "../selection/selectionStore.js";
    const { selected } = selectionStore;
    import { regionsStore } from "../regions/regionsStore.js";
    const { allRegions, fetchAll } = regionsStore;

    import Layout from "../Layout.svelte";
    import WitnessPanel from "../witness/WitnessPanel.svelte"
    import Loading from "../Loading.svelte";
    import Region from "../regions/Region.svelte";
    import SelectionBtn from "../selection/SelectionBtn.svelte";
    import Modal from "../Modal.svelte";
    import ExtractionButtons from "../regions/ExtractionButtons.svelte";
    import RegionsBtn from "../regions/RegionsBtn.svelte";
    import ActionButtons from "../regions/ActionButtons.svelte";
    import Similarity from "../regions/similarity/Similarity.svelte";
    import PageRegions from "../regions/PageRegions.svelte";
    import SelectionModal from "../selection/SelectionModal.svelte";
    import Vectorization from "../regions/vectorization/Vectorization.svelte";
    import Viewer from "../witness/ViewerIframe.svelte";
    import WitnessBtn from "../witness/WitnessBtn.svelte";

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

    $: selectedRegions = $selected(true);
    $: selectionLength = Object.keys(selectedRegions).length;
    $: areSelectedRegions = selectionLength > 0;

    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentRegionId = parseInt(baseUrl.split("regions/")[1].replace("/", ""));

    let activeTab = 0;

    const tabList = [
        appLang === "en" ? "Viewer" : "Visionneuse",
        appLang === "en" ? "All regions" : "Toutes les régions",
        appLang === "en" ? "Per page" : "Par page",
    ];
    if (modules.includes("similarity")) tabList.push(appLang === "en" ? "Similarity" : "Similarité");
    if (modules.includes("vectorization")) tabList.push(appLang === "en" ? "Vectorization" : "Vectorisation");
</script>

<Loading visible={$loading} />

<Modal />

<SelectionBtn {selectionLength} />

<Layout bind:activeTab {tabList}>
    <div slot="sidebar">
        <WitnessPanel {witness} {editUrl} {viewTitle} />
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
                    <div class="cell is-left">
                        <RegionsBtn {baseUrl} {currentRegionId} {activeTab}/>
                    </div>
                    <div class="cell">
                        {#if activeTab === 1 || activeTab === 2 }
                                <ActionButtons />
                        {:else if activeTab === 0}
                                <WitnessBtn {manifests} />
                        {/if}
                    </div>
                </div>
            </div>

            {#if activeTab === 0}
                <Viewer />

            {:else if activeTab === 1}
                <div class="grid is-gap-2 mt-5">
                    {#await fetchAll}
                        <div class="faded is-center">
                            {appLang === "en" ? "Retrieving regions..." : "Récupération des régions..."}
                        </div>
                    {:then _}
                        {#each Object.values($allRegions) as item (item.id)}
                            <Region {item} />
                        {:else}
                            <ExtractionButtons {currentRegionId} {baseUrl} />
                        {/each}
                    {:catch error}
                        <div>Error when retrieving regions: {error}</div>
                    {/await}
                </div>

            {:else if activeTab === 2}
                <PageRegions />

            {:else if activeTab === 3}
                <Similarity />

            {:else if activeTab === 4}
                <Vectorization />
            {/if}
        {/if}
    </div>
</Layout>

<SelectionModal isRegion={true} {selectionLength}>
    {#if areSelectedRegions}
        <div class="fixed-grid has-6-cols">
            <div class="grid is-gap-2">
                {#each Object.entries(selectedRegions) as [id, meta]}
                    <div class="selection cell">
                        <figure class="image is-64x64 card">
                            <img src="{refToIIIF(meta.img, meta.xywh, '96,')}" alt="" />
                            <div class="overlay is-center">
                                <span class="overlay-desc">{meta.title}</span>
                            </div>
                        </figure>
                        <button class="delete region-btn"
                            on:click={() => selectionStore.remove(id, regionsType)} />
                    </div>
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

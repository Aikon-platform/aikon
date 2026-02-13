<script>
    import { getContext } from "svelte";
    import { appLang } from "../../constants";
    import { toRegionItem } from "../utils.js";
    import SimilarRegion from "./SimilarRegion.svelte";
    import RegionModal from "../modal/RegionModal.svelte";
    import RegionCard from "../RegionCard.svelte";
    import PageView from "../modal/PageView.svelte";
    import SimilarityView from "../modal/SimilarityView.svelte";
    import QueryExpansionView from "../modal/QueryExpansionView.svelte";
    import Tabs from "../../ui/Tabs.svelte";

    export let items = [];
    export let loading = false;
    export let error = null;
    export let isPropagated = false;
    export let qImg;
    export let isInModal = false;
    export let noRegionsSelected = false;

    const qImgMetadata = getContext("qImgMetadata") || null;

    $: label = (() => {
        const plural = items.length > 1;
        if (isPropagated)
            return appLang === "fr"
                ? (plural ? "similarités propagées" : "similarité propagée")
                : (plural ? "propagated matches" : "propagated match");
        return appLang === "fr"
            ? (plural ? "images similaires" : "image similaire")
            : (plural ? "similar images" : "similar image");
    })();

    $: modalItems = items.map(([, , sImg]) => {
        const [wit, , canvas, xywh] = sImg.split(".")[0].split("_");
        return toRegionItem(sImg, wit, xywh, canvas);
    });

    $: currentScore = items[modalIndex]?.[0] ?? null;

    let modalOpen = false;
    let modalIndex = 0;

    const handleOpenModal = (e) => {
        modalIndex = e.detail.index ?? 0;
        modalOpen = true;
    };

    const tabs = [
        { id: "region", label: appLang === "en" ? "Main view" : "Vue principale" },
        { id: "page", label: appLang === "en" ? "Page View" : "Vue de la page" },
        { id: "similarity", label: appLang === "en" ? "Comparison" : "Comparaison" },
        { id: "expansion", label: appLang === "en" ? "Query Expansion" : "Expansion de requête" }
    ];
</script>

{#if loading}
    <div class="faded is-center">
        {isPropagated
            ? (appLang === "en" ? "Retrieving propagated regions..." : "Récupération de similarités propagées...")
            : (appLang === "en" ? "Retrieving similar regions..." : "Récupération des régions similaires...")}
    </div>
{:else if error}
    <div class="faded is-center">
        {appLang === "en" ? `Error: ${error}` : `Erreur : ${error}`}
    </div>
{:else}
    <div>
        <span class="m-2">{items.length} {label}</span>
        <div class="m-2 is-gap-2" class:grid={items.length > 0}>
            {#each items as [score, _, sImg, qRegions, sRegions, category, users, similarityType, similarityHash], i (sImg)}
                <SimilarRegion {qImg} {sImg} {score} {qRegions} {sRegions} {category} {users}
                               {similarityType} {similarityHash} index={i} {isInModal}
                               on:openModal={handleOpenModal} />
            {:else}
                <div class="faded is-center">
                    {#if !isPropagated && noRegionsSelected}
                        {appLang === "en" ? "No document selected. Select one to display results." : "Aucun document sélectionné. Sélectionnez-en un pour afficher les résultats."}
                    {:else}
                        {appLang === "en" ? "No similar regions" : "Pas de régions similaires"}
                    {/if}
                </div>
            {/each}
        </div>
    </div>

    <RegionModal items={modalItems} bind:currentIndex={modalIndex} bind:open={modalOpen}>
        <svelte:fragment let:item={currentItem}>
            <Tabs {tabs} let:activeTab>
                {#if activeTab === "region"}
                    <div class="modal-region">
                        <RegionCard item={currentItem} height="full" isInModal={true}/>
                    </div>
                {:else if activeTab === "page"}
                    <PageView item={currentItem}/>
                {:else if activeTab === "similarity" && qImgMetadata}
                    <SimilarityView queryItem={qImgMetadata} similarItem={currentItem} score={currentScore}/>
                {:else if activeTab === "expansion"}
                    <QueryExpansionView mainImgItem={currentItem}/>
                {/if}
            </Tabs>
        </svelte:fragment>
    </RegionModal>
{/if}

<style>
    .modal-region {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .modal-region :global(.region) {
        height: 100%;
    }
</style>

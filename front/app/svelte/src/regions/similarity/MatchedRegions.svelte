<script>
    import { appLang } from "../../constants";
    import SimilarRegion from "./SimilarRegion.svelte";
    import RegionModal from "../modal/RegionModal.svelte";
    import { RegionItem } from "../types.js";
    import RegionTabs from "../modal/RegionTabs.svelte";

    export let items = [];
    export let loading = false;
    export let error = null;
    export let isPropagated = false;
    export let qImg;
    export let isInModal = false;
    export let noRegionsSelected = false;
    export let downloadable = false;

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

    let modalOpen = false;
    let modalIndex = 0;

    const PAGE_SIZE = 10;
    let visibleCount = PAGE_SIZE;
    $: visibleItems = items.slice(0, visibleCount);
    $: hasMore = visibleCount < items.length;

    // Reset when items change
    $: items, visibleCount = PAGE_SIZE

    const handleOpenModal = (e) => {
        modalIndex = e.detail.index ?? 0;
        modalOpen = true;
    };

    $: modalItems = items.map(([, , sImg]) => RegionItem.fromImg(sImg));
    $: comparison = items[modalIndex] && { qImg, sImg: items[modalIndex][2] };
</script>

{#if loading}
    <div class="faded is-center py-3">
        {isPropagated
            ? (appLang === "en" ? "Retrieving propagated regions..." : "Récupération de similarités propagées...")
            : (appLang === "en" ? "Retrieving similar regions..." : "Récupération des régions similaires...")}
    </div>
{:else if error}
    <div class="faded is-center py-3">
        {appLang === "en" ? `Error: ${error}` : `Erreur : ${error}`}
    </div>
{:else}
    <div class="p-2">
        <span class="m-2">{items.length} {label}</span>
            <div class="m-4 is-gap-3" class:grid={items.length > 0}>
                {#each visibleItems as [score, _, sImg, , sRegions, category, users, similarityType, similarityHash], i (sImg)}
                    <SimilarRegion {qImg} {sImg} {score} {sRegions} {category} {users}
                                   {similarityType} {similarityHash} index={i} {isInModal} {downloadable}
                                   on:openModal={handleOpenModal}/>
                {:else}
                    <div class="faded is-center py-3">
                        {#if !isPropagated && noRegionsSelected}
                            {appLang === "en" ? "No document selected. Select one to display results." : "Aucun document sélectionné. Sélectionnez-en un pour afficher les résultats."}
                        {:else}
                            {appLang === "en" ? "No similar regions" : "Pas de régions similaires"}
                        {/if}
                    </div>
                {/each}
            </div>
            {#if hasMore}
                <div class="is-center py-3">
                    <button class="button is-small is-link is-outlined" on:click={() => visibleCount += PAGE_SIZE}>
                        {appLang === "en" ? `Load more` : `Charger plus`}
                    </button>
                </div>
            {/if}
        </div>

    {#if !isInModal}
        <RegionModal items={modalItems} bind:currentIndex={modalIndex} bind:open={modalOpen}>
            <svelte:fragment let:item={currentItem} let:anchored>
                <RegionTabs item={currentItem} comparison={anchored ? null : comparison}/>
            </svelte:fragment>
        </RegionModal>
    {/if}
{/if}

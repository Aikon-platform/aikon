<script>
    import { run } from 'svelte/legacy';

    import { appLang } from "../../constants";
    import SimilarRegion from "./SimilarRegion.svelte";
    import RegionModal from "../modal/RegionModal.svelte";
    import { RegionItem } from "../types.js";
    import RegionTabs from "../modal/RegionTabs.svelte";

    /**
     * @typedef {Object} Props
     * @property {any} [items]
     * @property {boolean} [loading]
     * @property {any} [error]
     * @property {boolean} [isPropagated]
     * @property {any} qImg
     * @property {boolean} [isInModal]
     * @property {boolean} [noRegionsSelected]
     * @property {boolean} [downloadable]
     */

    /** @type {Props} */
    let {
        items = [],
        loading = false,
        error = null,
        isPropagated = false,
        qImg,
        isInModal = false,
        noRegionsSelected = false,
        downloadable = false
    } = $props();

    let label = $derived((() => {
        const plural = items.length > 1;
        if (isPropagated)
            return appLang === "fr"
                ? (plural ? "similarités propagées" : "similarité propagée")
                : (plural ? "propagated matches" : "propagated match");
        return appLang === "fr"
            ? (plural ? "images similaires" : "image similaire")
            : (plural ? "similar images" : "similar image");
    })());

    let modalOpen = $state(false);
    let modalIndex = $state(0);

    const PAGE_SIZE = 10;
    let visibleCount = $state(PAGE_SIZE);
    let visibleItems = $derived(items.slice(0, visibleCount));
    let hasMore = $derived(visibleCount < items.length);

    // Reset when items change
    run(() => {
        items, visibleCount = PAGE_SIZE
    });

    const handleOpenModal = (e) => {
        modalIndex = e.detail.index ?? 0;
        modalOpen = true;
    };

    let modalItems = $derived(items.map(([, , sImg]) => RegionItem.fromImg(sImg)));
    let comparison = $derived(items[modalIndex] && { qImg, sImg: items[modalIndex][2] });
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
                    <button class="button is-small is-link is-outlined" onclick={() => visibleCount += PAGE_SIZE}>
                        {appLang === "en" ? `Load more` : `Charger plus`}
                    </button>
                </div>
            {/if}
        </div>

    {#if !isInModal}
        <RegionModal items={modalItems} bind:currentIndex={modalIndex} bind:open={modalOpen}>
            {#snippet children({ item: currentItem, anchored })}

                    <RegionTabs item={currentItem} comparison={anchored ? null : comparison} activeTab="similarity"/>

                            {/snippet}
        </RegionModal>
    {/if}
{/if}

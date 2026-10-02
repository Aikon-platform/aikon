<script>
    import { getContext } from "svelte";
    import { appName } from "../../constants.js";
    import { i18n, sendTo } from "../../utils.js";
    import { RegionItem } from "../types.js";
    import { similarityStore } from "../similarity/similarityStore.js";
    import RegionCard from "../RegionCard.svelte";
    import MergeOverlay from "./MergeOverlay.svelte";

    /**
     * DEDUPLICATION LOGIC
     * 1. List (`get_region_duplicates`):
     * Retrieve list of images in region_pairs of the same digitization with IoU > 0.5 with query image
     *
     * 2. Preview (`merge_regions_preview`, read-only):
     * Retrieve
     *    - the region to keep (the one in aiiinotate) otherwise the query image;
     *    - their IoU;
     *    - whether the dropped annotation will be deleted:
     *          -> automatically if both are annotated and IoU ≥ 0.9
     *          -> otherwise the user is asked;
     *    - the pairs whose categories would conflict.
     *
     * 3. Merge (`merge_regions`):
     *    - merges the pairs in the same digitization;
     *    - resolves category conflicts with the user's choice or the lowest category;
     *    - updates aiiinotate:
     *          -> if both regions are annotated, the dropped annotation is deleted;
     *          -> if only the dropped one is, its `xywh` is overwritten with bbox of the kept region;
     *    - rolls everything back if aiiinotate cannot be updated.
     * **/

    /** @type {import("../types.js").RegionItemType} */
    export let item;

    const setModalAnchor = getContext("setModalAnchor");
    $: qImg = (item instanceof RegionItem ? item : new RegionItem(item)).fullImg;

    const t = {
        addDuplicate: { en: "Add duplicate", fr: "Ajouter un doublon" },
        merge: { en: "Merge with query region", fr: "Fusionner avec la région requête" },
        setAnchor: { en: "Explore this region's duplicates", fr: "Explorer les doublons de cette région" },
        noDuplicate: { en: "No overlapping region on this page", fr: "Aucune région chevauchante sur cette page" },
        loading: { en: "Retrieving overlapping regions...", fr: "Récupération des régions chevauchantes..." },
        networkPb: { en: "Problem with network", fr: "Problème de réseau" },
    };

    let sImg = "";
    let preview = null;
    let candidates;
    const load = () => candidates = fetch(`${window.location.origin}/${appName}/similarity/duplicates/${encodeURIComponent(qImg)}`)
        .then(r => r.ok ? r.json() : Promise.reject(r.statusText));
    $: qImg, load();

    async function openMerge(img) {
        const data = await sendTo(`${appName}/similarity/merge-preview`, { q_img: qImg, s_img: img }, i18n("networkPb", t));
        if (data) preview = { q: qImg, s: img, ...data };
    }

    function onMerged({ detail: { kept } }) {
        preview = null;
        similarityStore.triggerRefresh();
        kept === qImg ? load() : setModalAnchor(RegionItem.fromImg(kept));
    }
</script>

{#if preview}
    <MergeOverlay {...preview} on:merged={onMerged} on:cancel={() => preview = null}/>
{:else}
    <div class="columns m-0">
        <div class="column is-4">
            <RegionCard item={RegionItem.fromImg(qImg)} height="full" isInModal={true} copyable={true} selectable={false}/>
            <div class="new-similarity control pt-2">
                <div class="tags has-addons" style="flex-wrap: nowrap">
                    <input bind:value={sImg} class="input is-small tag" type="text"
                           placeholder={i18n("addDuplicate", t)}/>
                    <button class="button is-small tag is-link is-center"
                            on:click={() => sImg.trim() && openMerge(sImg.trim())}>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                            <path fill="currentColor" d="M256 80c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 144L48 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l144 0 0 144c0 17.7 14.3 32 32 32s32-14.3 32-32l0-144 144 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-144 0 0-144z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
        <div class="column">
            {#await candidates}
                <div class="faded is-center py-3">{i18n("loading", t)}</div>
            {:then list}
                <div class="grid is-gap-3 has-3-cols m-4">
                    {#if list.length}
                        <div class="grid is-gap-3 has-3-cols m-4">
                            {#each list as {img, _} (img)}
                                <div class="cell">
                                    <RegionCard item={RegionItem.fromImg(img)} height={140} isInModal={true} copyable={false}
                                                selectable={false} downloadable={false}>
                                        <svelte:fragment slot="actions">
                                            <button class="button tag mb-1" title={i18n("merge", t)} on:click|stopPropagation={() => openMerge(img)}>
                                                <svg class="svg-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                                                    <path fill="currentColor" d="M80 56a24 24 0 1 1 0 48 24 24 0 1 1 0-48zm32.4 97.2c28-12.4 47.6-40.5 47.6-73.2c0-44.2-35.8-80-80-80S0 35.8 0 80c0 32.8 19.7 61 48 73.3l0 205.3C19.7 371 0 399.2 0 432c0 44.2 35.8 80 80 80s80-35.8 80-80c0-32.8-19.7-61-48-73.3l0-86.6c26.7 20.1 60 32 96 32l86.7 0c12.3 28.3 40.5 48 73.3 48c44.2 0 80-35.8 80-80s-35.8-80-80-80c-32.8 0-61 19.7-73.3 48L208 240c-49.9 0-91-38.1-95.6-86.8zM80 408a24 24 0 1 1 0 48 24 24 0 1 1 0-48zM344 272a24 24 0 1 1 48 0 24 24 0 1 1 -48 0z"></path>
                                                </svg>
                                            </button>
                                        </svelte:fragment>
                                    </RegionCard>
                                </div>
                            {/each}
                        </div>
                    {:else}
                        <div class="faded is-center py-3">{i18n("noDuplicate", t)}</div>
                    {/if}
                </div>
            {:catch e}
                <div class="faded is-center py-3">{e}</div>
            {/await}
        </div>
    </div>
{/if}

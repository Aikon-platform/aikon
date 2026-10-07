<script>
    import { appName } from "../../constants.js";
    import { i18n } from "../../utils.js";
    import { RegionItem } from "../types.js";
    import InputToggle from "../../ui/InputToggle.svelte";
    import RegionCard from "../RegionCard.svelte";
    import OverlayView from "./OverlayView.svelte";
    import PairCategoryToolbar from "../similarity/PairCategoryToolbar.svelte";

    export let qImg;
    export let sImg;

    const t = {
        query: {en: "Query image", fr: "Image requête"},
        target: {en: "Target image", fr: "Image cible"},
        overlay: {en: "Overlay view", fr: "Vue superposée"}
    }

    $: queryItem = RegionItem.fromImg(qImg);
    $: similarItem = RegionItem.fromImg(sImg);
    $: pairInfo = fetch(`${window.location.origin}/${appName}/similarity/pair?${new URLSearchParams({ q_img: qImg, s_img: sImg })}`)
        .then(r => r.ok ? r.json() : [])
        .catch(() => []);

    let overlay = false;
</script>

<div class="modal-similarity">
    <div class="modal-similarity-images" class:overlay-wrapper={overlay} class:side-by-side-wrapper={!overlay}>
        {#if overlay}
            <OverlayView {queryItem} {similarItem}/>
        {:else}
            <div class="side-by-side columns">
                <div class="column is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
                    <h3 class="title is-5">{i18n("query", t)}</h3>
                    <RegionCard item={queryItem} height="full" isInModal={true} downloadable={false}/>
                </div>
                <div class="column is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
                    <h3 class="title is-5">{i18n("target", t)}</h3>
                    <RegionCard item={similarItem} height="full" isInModal={true} downloadable={false}/>
                </div>
            </div>
        {/if}
    </div>
    <div class="is-flex is-align-items-center is-justify-content-center is-gap-2 m-auto">
        <InputToggle start={false} buttonDisplay={true} on:updateChecked={() => overlay = !overlay}
                     toggleLabel={i18n("overlay", t)}/>
        {#await pairInfo then [, , , , , category, users, similarityType, similarityHash]}
            <PairCategoryToolbar {qImg} {sImg} {category} users={users ?? []} {similarityType} {similarityHash}/>
        {/await}
    </div>
</div>

<style>
    .modal-similarity {
        display: grid;
        grid-template-columns: 100%;
        height: 100%;
        max-height: 100%;
        grid-template-rows: 90% 10%;
    }
    .modal-similarity-images.overlay-wrapper {
        display: grid;
        grid-template-rows: 1fr 0fr;
    }
    .modal-similarity-images > :global(*) {
        height: 100%;
    }
    .modal-similarity-images :global(img) {
        object-fit: contain;
        max-height: 100%;
        max-width: 100%;
        z-index: 2;
        padding: .25rem;
    }
    .side-by-side {
        height: 100%;
    }
</style>

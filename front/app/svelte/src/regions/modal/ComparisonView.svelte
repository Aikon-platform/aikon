<script>
    import { appLang } from "../../constants.js";
    import InputToggle from "../../ui/InputToggle.svelte";
    import RegionCard from "../RegionCard.svelte";
    import OverlayView from "./OverlayView.svelte";

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let queryItem;
    /** @type {RegionItemType} */
    export let similarItem;

    let overlay = false;
</script>

<div class="modal-similarity">
    <div class="modal-similarity-images" class:overlay-wrapper={overlay} class:side-by-side-wrapper={!overlay}>
        {#if overlay}
            <OverlayView {queryItem} {similarItem}/>
        {:else}
            <div class="side-by-side columns">
                <div class="column is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
                    <span>{appLang === "en" ? "Query image" : "Image requête"}</span>
                    <RegionCard item={queryItem} height="full" isInModal={true}/>
                </div>
                <div class="column is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
                    <span>{appLang === "en" ? "Similarity" : "Similarité"}</span>
                    <RegionCard item={similarItem} height="full" isInModal={true}/>
                </div>
            </div>
        {/if}
    </div>
    <div>
        <InputToggle start={false} buttonDisplay={true} on:updateChecked={() => overlay = !overlay}
                     toggleLabel={appLang === "en" ? "Overlay view" : "Vue superposée"}/>
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

<script>
    import { refToIIIF } from "../../utils";
    import { appLang } from "../../constants.js";

    import InputToggle from "../../ui/InputToggle.svelte";
    import ModalSimilarityOverlay from "./ModalSimilarityOverlay.svelte";
    import ModalSimilaritySideBySide from "./ModalSimilaritySideBySide.svelte";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */
    /** @typedef {import("./types.js").SimilarityOverlayType} SimilarityOverlayType */
    /** @typedef {import("./types.js").SimilaritySideBySideType} SimilaritySideBySideType */

    /////////////////////////////////////////////

    /** @type {RegionItemType} */
    export let mainImgItem;
    /** @type {RegionItemType} */
    export let compareImgItem;

    /** @type {SimilarityOverlayType} */
    const imgDataOverlay = {
        similarityImage: { href: refToIIIF(mainImgItem.img, mainImgItem.img.split("_").pop()), title: makeAlt(mainImgItem.title) },
        queryImage: { href: refToIIIF(compareImgItem.img, compareImgItem.img.split("_").pop()), title: makeAlt(compareImgItem.title) }
    }
    /** @type {SimilaritySideBySideType} */
    const imgDataSideBySide = {
        similarityImage: mainImgItem,
        queryImage: compareImgItem
    }
    /** @type {boolean} */
    let overlay = false;

    /////////////////////////////////////////////

    function makeAlt (title) {
        return appLang==="fr"
            ? `Vue principale de la région ${title}`
            : `Main view of region ${title}`;
    }

    const updateToggleOverlay = () => overlay = !overlay;
</script>

<div class="modal-similarity">
    <div class="modal-similarity-images {overlay ? 'overlay-wrapper' : 'side-by-side-wrapper'}">
        {#if overlay}
            <ModalSimilarityOverlay imgData={imgDataOverlay}/>
        {:else}
            <ModalSimilaritySideBySide imgData={imgDataSideBySide}/>
        {/if}
    </div>
    <div>
        <InputToggle start={false} buttonDisplay={true} on:updateChecked={updateToggleOverlay}
                     toggleLabel={appLang==="en" ? "Overlay view" : "Vue superposée"}/>
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
    :global(.modal-similarity-images > *) {
        height: 100%;
    }
    :global(.modal-similarity-images img) {
        object-fit: contain;
        max-height: 100%;
        max-width: 100%;
        z-index: 2;
        padding: .25rem;
    }
</style>

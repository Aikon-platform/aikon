<script>
    import { refToIIIF } from "../../utils";
    import { appLang } from "../../constants.js";

    import InputToggleCheckbox from "../../ui/InputToggleCheckbox.svelte";
    import ModalSimilarityOverlay from "./ModalSimilarityOverlay.svelte";
    import ModalSimilaritySideBySide from "./ModalSimilaritySideBySide.svelte";

    /** @typedef {import("./types.js").SimilarityImgDataType} SimilarityImgDataType */

    /////////////////////////////////////////////

    /** @type {string} */
    export let mainImg;
    /** @type {string} */
    export let compareImg;

    /** @type {SimilarityImgDataType} */
    const imgData = {
        similarityImage: { href: refToIIIF(mainImg), title: makeAlt(mainImg) },
        queryImage: { href: refToIIIF(compareImg), title: makeAlt(compareImg) }
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

<div>
    <div class="modal-similarity-images">
        {#if overlay}
            <ModalSimilarityOverlay  imgData={imgData}></ModalSimilarityOverlay>
        {:else}
            <ModalSimilaritySideBySide imgData={imgData}></ModalSimilaritySideBySide>
        {/if}
    </div>
    <div>
        <InputToggleCheckbox start={false}
                             buttonDisplay={true}
                             checkboxLabel={appLang==="en" ? "Overlay view" : "Vue superposée"}
                             on:updateChecked={updateToggleOverlay}
        ></InputToggleCheckbox>
    </div>
</div>

<style>
    :global(.modal-similarity-images img) {
        object-fit: contain;
        max-height: 80%;
        max-width: 80%;
        z-index: 2;
    }
</style>

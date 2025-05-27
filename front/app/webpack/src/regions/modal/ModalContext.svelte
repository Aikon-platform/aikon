<script>
    import { refToIIIF } from "../../utils.js";

    import Region from "../Region.svelte";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let mainImgItem;
    console.log(mainImgItem)
    const fullPageUrl = refToIIIF(mainImgItem.img, "full", "full");
    // let fullPageUrl = mainImgItem.url.replace(/\/[\d,]+\/full\/\d+\//, "\.jpg/full/full/0/")
</script>

<div class="modal-context-outer p-2">
    <div class="modal-context-wrapper">
        <img class="modal-context-full-page"
            src={fullPageUrl}
            alt="full page stuff"
        >
    </div>
</div>

<style>
    .modal-context-outer {
        height: 100%;
    }
    .modal-context-wrapper {
        height: 100%;
        width: 100%;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .modal-context-full-page {
        object-fit: contain;
        max-height: 100%;
        max-width: 100%;
    }
</style>

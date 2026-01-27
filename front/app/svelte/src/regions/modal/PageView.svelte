<script>
    import { refToIIIF, refToIIIFInfo } from "../../utils.js";
    import { appLang } from "../../constants.js";

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let item;

    $: fullPageUrl = refToIIIF(item.img ?? item.ref, "full", "full");
    $: iiifInfoUrl = refToIIIFInfo(item.img ?? item.ref);
    $: xywh = item.xywh.map(Number);

    // retrieve full page dimension
    $: xywhRelPromise = fetch(iiifInfoUrl)
        .then(r => r.json())
        .then(({ width, height }) => [
            (xywh[0] / width) * 100,
            (xywh[1] / height) * 100,
            (xywh[2] / width) * 100,
            (xywh[3] / height) * 100
        ]);
</script>

<div class="modal-context-outer pb-4">
    <div class="modal-context-wrapper">
        <img class="card modal-context-full-page" src={fullPageUrl} alt={appLang === "fr" ? "Vue de la page d'où la région est extraite" : "View of the page the region is extracted from"}/>
        {#await xywhRelPromise then [left, top, width, height]}
            <div class="modal-context-bbox" style:left="{left}%" style:top="{top}%" style:width="{width}%" style:height="{height}%"/>
        {/await}
    </div>
</div>

<style>
    .modal-context-outer {
        height: 100%;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .modal-context-wrapper {
        height: 100%;
        max-width: 100%;
        position: relative;
        display: inline-block;
    }
    .modal-context-full-page {
        object-fit: contain;
        max-height: 100%;
        max-width: 100%;
        height: 100%;
    }
    .modal-context-bbox {
        position: absolute;
        border: 3px solid var(--bulma-link);
    }
</style>

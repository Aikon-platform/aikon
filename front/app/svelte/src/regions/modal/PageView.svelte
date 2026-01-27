<script>
    import { appLang } from "../../constants.js";
    import NavigationArrow from "../../ui/NavigationArrow.svelte";
    import {RegionItem} from "../types.js";

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let item;

    let canvasOffset = 0;

    $: currentPage = new RegionItem(item);
    $: currentCanvas = currentPage.canvasNb + canvasOffset;
    $: fullPageUrl = currentPage.urlForCanvas(currentCanvas);
    $: iiifInfoUrl = currentPage.infoUrlForCanvas(currentCanvas);
    $: xywh = currentPage.coord;

    // retrieve full page dimension
    $: xywhRelPromise = fetch(iiifInfoUrl)
        .then(r => r.json())
        .then(({ width, height }) => [
            (xywh[0] / width) * 100,
            (xywh[1] / height) * 100,
            (xywh[2] / width) * 100,
            (xywh[3] / height) * 100
        ]);

    const changePage = (delta) => canvasOffset += delta;
</script>

<div class="modal-context-outer is-flex-direction-column pb-4">
    <div class="has-text-centered m-2">
        <p class="tag is-small has-text-grey">Page {currentCanvas}</p>
    </div>
    <div class="modal-context-wrapper">
        <NavigationArrow direction="left" delta={-1} navigationFct={changePage}/>
        <img class="card modal-context-full-page" src={fullPageUrl} alt={appLang === "fr" ? "Vue de la page d'où la région est extraite" : "View of the page the region is extracted from"}/>
        {#if canvasOffset === 0}
            {#await xywhRelPromise then [left, top, width, height]}
                <div class="modal-context-bbox" style:left="{left}%" style:top="{top}%" style:width="{width}%" style:height="{height}%"/>
            {/await}
        {/if}
        <NavigationArrow direction="right" delta={1} navigationFct={changePage}/>
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

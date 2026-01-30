<script>
    import { appLang } from "../../constants.js";
    import NavigationArrow from "../../ui/NavigationArrow.svelte";
    import {RegionItem} from "../types.js";
    import {i18n} from "../../utils.js";

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let item;

    let canvasOffset = 0;
    let maxPage = null;
    let previousItemId = item.id;

    // reset canvas offset when item changes
    $: if (item.id !== previousItemId) {
        canvasOffset = 0;
        maxPage = null;
        previousItemId = item.id;
    }

    $: currentPage = new RegionItem(item);
    $: currentCanvas = currentPage.canvasNb + canvasOffset;
    $: fullPageUrl = currentPage.urlForCanvas(currentCanvas, "full");
    $: iiifInfoUrl = currentPage.infoUrlForCanvas(currentCanvas);
    $: xywh = currentPage.coord;

    const t = {
        next: { en: "Next page", fr: "Page suivante" },
        prev: { en: "Previous page", fr: "Page précédente" },
    };

    $: xywhRelPromise = fetch(iiifInfoUrl)
        .then(r => {
            if (!r.ok) {
                if (maxPage === null) maxPage = currentCanvas - 1;
                throw new Error('Page not found');
            }
            return r.json();
        })
        .then(({ width, height }) => [
            (xywh[0] / width) * 100,
            (xywh[1] / height) * 100,
            (xywh[2] / width) * 100,
            (xywh[3] / height) * 100
        ])
        .catch(() => null);

    const changePage = async (delta) => {
        const nextCanvas = currentCanvas + delta;
        if (nextCanvas < 1) return;
        if (maxPage !== null && nextCanvas > maxPage) return;

        const response = await fetch(
            currentPage.infoUrlForCanvas(nextCanvas)
        );

        if (!response.ok) {
            maxPage = currentCanvas;
            return;
        }
        canvasOffset += delta;
    };
</script>

<div class="modal-context-outer is-flex-direction-column pb-4">
    <div class="has-text-centered m-2">
        <a class="tag button is-small has-text-grey mt-3" href={currentPage.urlForMirador(currentCanvas)} target="_blank">
            Page {currentCanvas}
        </a>
    </div>
    <div class="modal-context-wrapper my-3">
        {#if currentCanvas !== 1}
            <NavigationArrow direction="left" delta={-1} navigationFct={changePage} css={"margin-left: -6em;"} icon={"caret"} text={i18n("prev", t)}/>
        {/if}
        <img class="card modal-context-full-page" src={fullPageUrl} alt={appLang === "fr" ? "Vue de la page d'où la région est extraite" : "View of the page the region is extracted from"}/>
        {#if canvasOffset === 0}
            {#await xywhRelPromise then [left, top, width, height]}
                <div class="modal-context-bbox" style:left="{left}%" style:top="{top}%" style:width="{width}%" style:height="{height}%"/>
            {/await}
        {/if}
        {#if currentCanvas !== maxPage}
            <NavigationArrow direction="right" delta={1} navigationFct={changePage} css={"margin-right: -6em;"} icon={"caret"} text={i18n("next", t)}/>
        {/if}
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

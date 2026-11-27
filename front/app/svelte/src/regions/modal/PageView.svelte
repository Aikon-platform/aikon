<script>
    import { run } from 'svelte/legacy';

    import { appLang } from "../../constants.js";
    import NavigationArrow from "../../ui/NavigationArrow.svelte";
    import {RegionItem} from "../types.js";
    import {i18n} from "../../utils.svelte.js";

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */


    /**
     * @typedef {Object} Props
     * @property {RegionItemType} item
     * @property {boolean} [showNav]
     * @property {any} [height]
     */

    /** @type {Props} */
    let { item, showNav = true, height = null } = $props();


    let canvasOffset = $state(0);
    let maxPage = $state(null);
    let previousItemId = $state(item.id);




    const maybeResetMaxPage = () => {
        if (maxPage === null) maxPage = currentCanvas - 1;
    }

    const t = {
        next: { en: "Next page", fr: "Page suivante" },
        prev: { en: "Previous page", fr: "Page précédente" },
    };

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
    // reset canvas offset when item changes
    run(() => {
        if (item.id !== previousItemId) {
            canvasOffset = 0;
            maxPage = null;
            previousItemId = item.id;
        }
    });
    let currentPage = $derived(new RegionItem(item));
    let xywh = $derived(currentPage.coord);
    let currentCanvas = $derived(currentPage.canvasNb + canvasOffset);
    let fullPageUrl = $derived(currentPage.urlForCanvas(currentCanvas, "full"));
    let iiifInfoUrl = $derived(currentPage.infoUrlForCanvas(currentCanvas));
    let xywhRelPromise = $derived(fetch(iiifInfoUrl)
        .then(r => {
            if (!r.ok) {
                maybeResetMaxPage();
                throw new Error("Page not found");
            }
            return r.json();
        })
        .then(({ width, height }) => [
            (xywh[0] / width) * 100,
            (xywh[1] / height) * 100,
            (xywh[2] / width) * 100,
            (xywh[3] / height) * 100
        ])
        .catch((e) => {
            console.error(`PageView: error fetching ${iiifInfoUrl}`, e);
        }));
</script>

<div class="modal-context-outer is-flex-direction-column pb-4">
    <div class="has-text-centered m-2">
        <a class="tag button is-small has-text-grey mt-3" href={currentPage.urlForMirador(currentCanvas-1)} target="_blank">
            Page {currentCanvas}
        </a>
    </div>
    <div class="modal-context-wrapper mb-3" style:height={height}>
        {#if showNav && currentCanvas !== 1}
            <NavigationArrow direction="left" delta={-1} navigationFct={changePage} css="margin-left: -6em;" icon="circle" text={i18n("prev", t)}/>
        {/if}
        <img class="card modal-context-full-page" src={fullPageUrl} alt={appLang === "fr" ? "Vue de la page d'où la région est extraite" : "View of the page the region is extracted from"}/>
        {#if canvasOffset === 0}
            {#await xywhRelPromise then [left, top, width, height]}
                <div class="modal-context-bbox" style:left="{left}%" style:top="{top}%" style:width="{width}%" style:height="{height}%"></div>
            {/await}
        {/if}
        {#if showNav && currentCanvas !== maxPage}
            <NavigationArrow direction="right" delta={1} navigationFct={changePage} css="margin-right: -6em;" icon="circle" text={i18n("next", t)}/>
        {/if}
    </div>
</div>

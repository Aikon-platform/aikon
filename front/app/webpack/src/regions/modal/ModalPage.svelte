<script>
    import { refToIIIF, refToIIIFInfo } from "../../utils.js";

    import { appLang } from "../../constants.js";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */

    //////////////////////////////////////////////

    // TODO fix because somehow this is not working when opened in the context of the similarity view

    /** @type {RegionItemType} */
    export let mainImgItem;

    const fullPageUrl = refToIIIF(mainImgItem.img, "full", "full");
    const iiifInfoUrl = refToIIIFInfo(mainImgItem.img);
    const xywh = mainImgItem.xywh.map(Number);

    // fetch full image dimensions in the image's info.json, then convert in relative coordinates
    const xywhRelPromise = fetch(iiifInfoUrl)
        .then(r => r.json())
        .then(data => [
            xywh[0] / data.width,
            xywh[1] / data.height,
            xywh[2] / data.width,
            xywh[3] / data.height
        ].map(x => x*100));
</script>

<div class="modal-context-outer pb-4">
    <div class="modal-context-wrapper">
        <img class="card modal-context-full-page"
             src={fullPageUrl}
             alt={
                appLang==="fr"
                ? "Vue de la page d'où la région est extraite"
                : "View of the page the region is extracted from"
            }
        >
        {#await xywhRelPromise then xywhRel}
            <div class="modal-context-bbox"
                 style:left="{xywhRel[0]}%"
                 style:top="{xywhRel[1]}%"
                 style:width="{xywhRel[2]}%"
                 style:height="{xywhRel[3]}%"
                 aria-description={
                    appLang==="fr"
                    ? "Position de la région extraite sur la page"
                    : "Position of the extracted region on the page"
                }
            ></div>
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

<script>
    import { refToIIIF, refToIIIFInfo } from "../../utils.js";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let mainImgItem;

    const fullPageUrl = refToIIIF(mainImgItem.img, "full", "full");
    const iiifInfoUrl = refToIIIFInfo(mainImgItem.img);

    // fetch full image dimensions in the image's info.json, then convert in relative coordinates
    //NOTE the coordinates in `mainImgItem.xywh` are actually expressed in `xywh`, the key sent by Django simply has the wrong name.
    const xywhRelPromise = fetch(iiifInfoUrl)
        .then(r => r.json())
        .then(data => [
            Number(mainImgItem.xywh[0]) / data.width,
            Number(mainImgItem.xywh[1]) / data.height,
            Number(mainImgItem.xywh[2]) / data.width,
            Number(mainImgItem.xywh[3]) / data.height
        ].map(x => x*100));

</script>

<div class="modal-context-outer pb-4">
    <div class="modal-context-wrapper">
        <img class="card modal-context-full-page"
             src={fullPageUrl}
             alt="full page stuff"
        >
        {#await xywhRelPromise then xywhRel}
            <div class="modal-context-bbox"
                 style:left="{xywhRel[0]}%"
                 style:top="{xywhRel[1]}%"
                 style:width="{xywhRel[2]}%"
                 style:height="{xywhRel[3]}%"
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
    }
    .modal-context-bbox {
        position: absolute;
        border: 2px solid red;
    }
</style>

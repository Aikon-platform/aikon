<script>
    import { refToIIIF, refToIIIFInfo } from "../../utils.js";

    import Region from "../Region.svelte";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let mainImgItem;

    ///////////////////////////////////////////////

    const fullPageUrl = refToIIIF(mainImgItem.img, "full", "full");
    const iiifInfoUrl = refToIIIFInfo(mainImgItem.img);

    // fetch full image dimensions in the image's info.json, then convert in relative coordinates
    const xywhRelPromise = fetch(iiifInfoUrl)
        .then(r => r.json())
        .then(data => [
            Number(mainImgItem.xyhw[0]) / data.width,
            Number(mainImgItem.xyhw[1]) / data.height,
            Number(mainImgItem.xyhw[2]) / data.width,
            Number(mainImgItem.xyhw[3]) / data.height
        ].map(x => x*100));

    ///////////////////////////////////////////////

    console.log(mainImgItem)
    console.log("holleeeooo", mainImgItem.xyhw[0]
                            , mainImgItem.xyhw[1]
                            , mainImgItem.xyhw[2]
                            , mainImgItem.xyhw[3]
                            , iiifInfoUrl);
    // let fullPageUrl = mainImgItem.url.replace(/\/[\d,]+\/full\/\d+\//, "\.jpg/full/full/0/")
</script>

<div class="modal-context-outer p-2">
    <div class="modal-context-wrapper">
            <img class="modal-context-full-page"
                 src={fullPageUrl}
                 alt="full page stuff"
             >
             {#await xywhRelPromise then xywhRel}
                 <div class="modal-context-bbox"
                      style:left="{xywhRel[0]}%"
                      style:top="{xywhRel[1]}%"
                      style:height="{xywhRel[3]}%"
                      style:width="{xywhRel[2]}%"
                 ></div>
             {/await}
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
        background-color: pink;
    }
    .iii {
        background-color: green;
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

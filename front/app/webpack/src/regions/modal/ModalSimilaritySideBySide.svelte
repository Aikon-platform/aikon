<script>
    import { getContext } from "svelte";

    import { appLang } from "../../constants.js";
    import { getDesc } from "../similarity/utils.js";

    import Region from "../Region.svelte";

    /** @typedef {import("./types.js").SimilarityImgDataType} SimilarityImgDataType */
    /** @typedef {import("../similarity/types.js").SimilarityPairType} SimilarityPairType */

    //////////////////////////////////////////////

    /** @type {SimilarityImgDataType} */
    export let imgData;

    /** @type {SimilarityPairType} */
    const similarityPairContext = getContext("similarityPair");

    const windowUrl = new URL(window.location.href)
    const baseUrl = windowUrl.origin;
    const pathUrl = windowUrl.pathname;

    const [qWit, qDigit, qCanvas, qXywh] = similarityPairContext.qImg.split('.')[0].split('_');
    const [sWit, sDigit, sCanvas, sXywh] = similarityPairContext.sImg.split('.')[0].split('_');
    const qRegionRef = `${qWit}_${qDigit}`;
    const sRegionRef = `${sWit}_${sDigit}`;

    /** @type {{ queryImage: Promise<string>, similarityImage: Promise<string> }}*/
    const descPromiseObj = {
        queryImage: getDesc(qRegionRef, similarityPairContext.similarityType, similarityPairContext.score, qCanvas, baseUrl, pathUrl, true, false),
        similarityImage: getDesc(sRegionRef, similarityPairContext.similarityType, similarityPairContext.score, sCanvas, baseUrl, pathUrl, true, true),
    }
</script>

<div class="side-by-side columns">
    {#each ["queryImage", "similarityImage"] as k}
        <div class="img-legend-wrapper column is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
            <span>{
                k==="queryImage" && appLang==="fr"
                ? "Image requête"
                : k==="similarityImage" && appLang==="fr"
                ? "Similarité"
                : k==="queryImage" && appLang==="en"
                ? "Query image"
                : "Similarity"
            }</span>
            <Region item={imgData[k]}
                    descPromise={descPromiseObj[k]}
                    height="full"
            ></Region>
        </div>
    {/each}
</div>

<style>

</style>

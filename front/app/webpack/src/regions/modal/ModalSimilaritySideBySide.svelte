<script>
    import { appLang } from "../../constants.js";

    /** @typedef {import("./types.js").SimilarityImgDataType} SimilarityImgDataType */

    /** @type {SimilarityImgDataType} */
    export let imgData;
</script>

<div>
    <div class="columns">
        {#each ["queryImage", "similarityImage"] as imgDataKey}
            <div class="column is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
                <span>{
                    imgDataKey==="queryImage" && appLang==="fr"
                    ? "Image requête"
                    : imgDataKey==="similarityImage" && appLang==="fr"
                    ? "Similarité"
                    : imgDataKey==="queryImage" && appLang==="en"
                    ? "Query image"
                    : "Similarity"
                }</span>
                <img src={imgData[imgDataKey].href}
                     alt={imgData[imgDataKey].title}
                >
            </div>
        {/each}
    </div>
</div>

<style>

</style>

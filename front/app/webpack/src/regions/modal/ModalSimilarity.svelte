<script>
    import { refToIIIF } from "../../utils";
    import { appLang } from "../../constants.js";

    ////////////////////////////////

    /** @type {string} */
    export let mainImg;
    /** @type {string} */
    export let compareImg;

    const mainImgHref = refToIIIF(mainImg);
    const compareImgHref = refToIIIF(compareImg);
</script>

<div>
    <div class="columns">
        {#each [compareImgHref, mainImgHref] as imgHref, i}
            <div class="column is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
                <span>{
                    i===0 && appLang==="fr"
                    ? "Image requête"
                    : i===1 && appLang==="fr"
                    ? "Similarité"
                    : i===0 && appLang==="en"
                    ? "Query image"
                    : "Similarity"
                }</span>
                <img src={imgHref}
                     alt="Main view of region {imgHref}"
                >
            </div>
        {/each}
    </div>
</div>

<style>
    img {
        object-fit: contain;
        max-height: 80%;
        max-width: 80%;
    }
</style>

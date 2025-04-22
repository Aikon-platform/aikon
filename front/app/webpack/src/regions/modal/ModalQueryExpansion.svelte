<script>
    import { appLang } from "../../constants.js";

    import SimilarityRow from "../similarity/SimilarityRow.svelte";

    ////////////////////////////////////////

    /** @type {string} */
    export let mainImg;

    /** @type {string} */
    const mainImgWitnessId = mainImg.match(/wit(\d+)/)[1]

    const similarityViewUrl = buildRedirectionUrl()

    ////////////////////////////////////////

    /** @returns {string} */
    function buildRedirectionUrl() {
        const u = new URL(window.location.origin);
        u.pathname = `${new URL(window.location).pathname.split("/")[1]}/witness/${mainImgWitnessId}/regions/`
        u.searchParams.set("tab", "similarity");
        console.log(u);
        return u.href;
    }
</script>

<div class="is-flex is-align-items-center is-justify-content-end">
    <a href={similarityViewUrl}>
        <button class="button is-link">{ appLang==="fr" ? "Voir toutes les similarités pour ce document" : "View all similarities for this document"}</button>
    </a>
</div>
<SimilarityRow qImg={mainImg}></SimilarityRow>

<style></style>

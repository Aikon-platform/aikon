<script>
    import { appLang } from "../../constants.js";

    import SimilarityRow from "../similarity/SimilarityRow.svelte";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */

    ////////////////////////////////////////

    /** @type {RegionItemType} */
    export let mainImgItem;

    /** @returns {string} */
    function buildRedirectionUrl() {
        const mainImgWitnessId = mainImgItem.img.match(/wit(\d+)/)[1];
        const u = new URL(window.location.origin);
        u.pathname = `${new URL(window.location).pathname.split("/")[1]}/witness/${mainImgWitnessId}/regions/`
        u.searchParams.set("tab", "similarity");
        return u.href;
    }
</script>

<div class="is-flex is-align-items-center is-justify-content-end">
    <a href={buildRedirectionUrl()}>
        <button class="button is-link is-small">{
            appLang === "fr"
            ? "Voir toutes les similarités pour ce document"
            : "View all similarities for this document"
        }</button>
    </a>
</div>
<SimilarityRow qImg={mainImgItem.img}/>

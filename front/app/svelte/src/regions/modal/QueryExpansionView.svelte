<script>
    import { appLang } from "../../constants.js";
    import { RegionItem } from "../types.js";

    import SimilarityRow from "../similarity/SimilarityRow.svelte";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */

    ////////////////////////////////////////

    /** @type {RegionItemType} */
    export let item;

    $: regionItem = item instanceof RegionItem ? item : new RegionItem(item);

    /** @returns {string} */
    function buildRedirectionUrl() {
        const u = new URL(window.location.origin);
        u.pathname = `${new URL(window.location).pathname.split("/")[1]}/witness/${regionItem.witnessId}/regions/`
        u.searchParams.set("tab", "similarity");
        return u.href;
    }
</script>

<div class="is-flex is-align-items-center is-justify-content-end">
    <a href={buildRedirectionUrl()}>
        <button class="button is-link is-small">
            {appLang === "fr" ?
                "Voir toutes les similarités pour ce document" :
                "View all similarities for this document"}
        </button>
    </a>
</div>

<SimilarityRow qImg={regionItem.fullImg} isInModal={true}/>

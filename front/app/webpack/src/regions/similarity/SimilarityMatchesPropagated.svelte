<script>
    import { setContext } from "svelte";

    import SimilarRegions from "./SimilarRegions.svelte";
    import IconTooltip from "../../ui/IconTooltip.svelte";

    import { appLang, csrfToken } from '../../constants.js';
    import { similarityStore } from "./similarityStore";

    ////////////////////////////////////

    export let qImg;

    const { propagateParams, selectedRegions } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');
    const tooltipText =
        appLang==="en"
        ? "Propagated matches are exact matches to images that have an exact match with the current image. There may be up to 5 exact matches connecting the current image and propagated images."
        : "Les correspondances propagées correspondent à des correspondances exactes à des images ayant une correspondance exacte avec l'image actuelle. Il peut y avoir jusqu'à 5 images reliant l'image actuelle à une correspondance propagée.";

    let propagatedMatchesPromise;

    setContext("similarityPropagatedContext", true);  // bool. true if it's a propagated similarity match, false if it's any other match

    ////////////////////////////////////

    /**
     * @param {boolean} filterByRegions
     * @param {number[]} recursionDepth
     * @param {RegionsType} selection
     */
    const getPropagatedMatches = async (filterByRegions, recursionDepth, selection) =>
        fetch(`${baseUrl}propagated-matches/${qImg}`, {
            method: "POST",
            body: JSON.stringify({
                regionsIds: Object.values(selection[currentPageId]).map(r => r.id),
                filterByRegions: filterByRegions,
                recursionDepth: recursionDepth
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },

        }).then(r => r.json());

    propagateParams.subscribe((newPropagatedParams) => {
        propagatedMatchesPromise = getPropagatedMatches(
            newPropagatedParams.filterByRegions,
            newPropagatedParams.recursionDepth,
            $selectedRegions
        )
    })


</script>

<div class="block matches-suggestion-wrapper">
    <div class="matches-suggestion">
        <div class="block">
            {#await propagatedMatchesPromise then propagatedImgs}
                {propagatedImgs.length} propagated match{propagatedImgs.length > 1 ? "es" : "" }
                <IconTooltip iconifyIcon="material-symbols:help-outline"
                                altText={ appLang==="en" ? "Display help" : "Afficher une explication"}
                                tooltipText={tooltipText}
                ></IconTooltip>
            {/await}
        </div>
        <div class="grid is-gap-2">
            <SimilarRegions qImg={qImg}
                           sImgsPromise={propagatedMatchesPromise}
                           displayType="suggestionMatches"
            ></SimilarRegions>
        </div>
    </div>
</div>

<style type="text/css">
.matches-suggestion-wrapper {
    border: 1px solid var(--bulma-border);
    border-radius: 1em;
}
.matches-suggestion {
    margin: 1.5rem;
}
</style>

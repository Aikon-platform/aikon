<script>
    import SimilarRegions from "./SimilarRegions.svelte";
    import TooltipGeneric from "../../TooltipGeneric.svelte";
    import { appLang } from '../../constants.js';

    export let qImg;

    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const getMatchesSuggestionImgs = async () =>
        fetch(`${baseUrl}suggested-regions/${qImg}`).then(r => r.json());
    const tooltipText =
        appLang==="en"
        ? "Suggested matches are exact matches to images that have an exact match with the current image. There may be up to 5 exact matches connecting the current image and suggested images."
        : "Les correspondances suggerées correspondent à des correspondances exactes à des images ayant une correspondance exacte avec l'image actuelle. Il peut y avoir jusqu'à 5 images reliant l'image actuelle à une correspondance suggerée.";

    $: suggestionImgsPromise = getMatchesSuggestionImgs()
</script>

<div class="block matches-suggestion-wrapper">
    <div class="matches-suggestion">
        <div class="block">
            {#await suggestionImgsPromise then suggestionImgs}
                {suggestionImgs.length} suggested regions
                <TooltipGeneric iconifyIcon="material-symbols:help-outline"
                                altText={ appLang==="en" ? "Display help" : "Afficher une explication"}
                                tooltipText={tooltipText}
                ></TooltipGeneric>
            {/await}
        </div>
        <div class="grid is-gap-2">
            <SimilarRegions qImg={qImg}
                           sImgsPromise={suggestionImgsPromise}
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

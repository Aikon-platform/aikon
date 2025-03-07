<script>
    import SimilarRegions from "./SimilarRegions.svelte";

    export let qImg;

    const baseUrl = `${window.location.origin}${window.location.pathname}`;

    const getMatchesSuggestionImgs = async () =>
        fetch(`${baseUrl}suggested-regions/${qImg}`).then(r => r.json())

    $: suggestionImgsPromise = getMatchesSuggestionImgs()
</script>

<div style="border: dotted 5px purple">
    <span>
        {#await suggestionImgsPromise}
            WAITING :'(
        {:then suggestionImgs}
            {suggestionImgs.length} suggestions retrieved
        {/await}
    </span>
    <div class="grid is-gap-2">
        <SimilarRegions qImg={qImg} sImgsPromise={suggestionImgsPromise}></SimilarRegions>
    </div>
</div>

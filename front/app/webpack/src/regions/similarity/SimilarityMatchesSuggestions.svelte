<script>
    import SimilarRegions from "./SimilarRegions.svelte";

    export let qImg;

    const baseUrl = `${window.location.origin}${window.location.pathname}`;

    const getMatchesSuggestionImgs = async () =>
        fetch(`${baseUrl}suggested-regions/${qImg}`).then(r => r.json())

    $: matchesSuggestionImgs = getMatchesSuggestionImgs()

</script>

<div>
    <div class="grid is-gap-2" style="border: dotted 5px white">
        <SimilarRegions qImg={qImg} sImgsPromise={matchesSuggestionImgs}></SimilarRegions>
    </div>
</div>

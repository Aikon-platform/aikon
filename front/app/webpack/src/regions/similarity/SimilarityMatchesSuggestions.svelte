<script>
    import { writable } from "svelte/store";

    export let qImg;

    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const suggestionImgs = writable([]);

    async function getSuggestionImgs() {
        fetch(`${baseUrl}suggested-regions/${qImg}`)
        .then(r => r.json()).then(responseBody => suggestionImgs.set(responseBody))
        .catch(err => console.error("ERROR ON SimilarityMatchesSuggestions:", err))
    }
    getSuggestionImgs();


</script>

<div>
    <h1 style="background-color: orange">{qImg}</h1>
</div>

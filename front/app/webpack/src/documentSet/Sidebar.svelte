<script>
    import { createEventDispatcher } from 'svelte';

    export let availableCorpus = {};
    export let selectedCorpus = "";
    export let corpusStats = null;

    const dispatch = createEventDispatcher();

    function handleCorpusChange(event) {
        dispatch('corpusSelect', { name: event.target.value });
    }
</script>

<div class="m-4">
    <h2 class="title is-5">Corpus Selection</h2>

    <div class="field">
        <label class="label" for="corpus">Select Corpus</label>
        <div class="control">
            <div class="select is-fullwidth">
                <select id="corpus" bind:value={selectedCorpus} on:change={handleCorpusChange}>
                    <option value="">-- Choose a corpus --</option>
                    {#each Object.keys(availableCorpus) as name}
                        <option value={name}>{name}</option>
                    {/each}
                </select>
            </div>
        </div>
    </div>

    {#if corpusStats}
        <div class="content is-small mt-4">
            <h3 class="title is-6">Corpus Information</h3>
            <ul>
                <li><strong>Nodes:</strong> {corpusStats.nodeCount}</li>
                <li><strong>Links:</strong> {corpusStats.linkCount}</li>
                <li><strong>Sub-corpus:</strong> {corpusStats.subCorpusCount}</li>
                <li><strong>Documents:</strong> {corpusStats.docCount}</li>
            </ul>
        </div>
    {/if}

    <div id="regions-info"></div>
</div>

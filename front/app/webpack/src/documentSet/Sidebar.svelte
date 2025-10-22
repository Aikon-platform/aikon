<script>
    export let docSetStats = null;
    // todo display document set stats
</script>

<div class="m-4">
    <h2 class="title is-5">Document set</h2>

    {#if docSetStats}
        <div class="content is-small mt-4">
            <h3 class="title is-6">Corpus Information</h3>
            <ul>
                <li><strong>Nodes:</strong> {docSetStats.nodeCount}</li>
                <li><strong>Links:</strong> {docSetStats.linkCount}</li>
                <li><strong>Sub-corpus:</strong> {docSetStats.subCorpusCount}</li>
                <li><strong>Documents:</strong> {docSetStats.docCount}</li>
            </ul>
        </div>
    {/if}

    <div id="legend"></div>
</div>

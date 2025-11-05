<script>
    import Layout from '../Layout.svelte';
    import Sidebar from './Sidebar.svelte';
    import NetworkVisualization from './NetworkVisualization.svelte';
    import {createDocumentSetStore} from './documentSetStore.js';
    export let docSet;

    const {
        imageNetwork,
        documentNetwork,
        regionsMetadata,
        docSetStats,
        fetchPairs,
        error,
        selectedNodes,
        updateSelectedNodes
    } = createDocumentSetStore(docSet.id);
    let activeTab = 0;

    $: visualizationTitle = activeTab === 0 ? "Image regions network" : "Witness network";
</script>

<Layout bind:activeTab>
    <div slot="sidebar">
        <Sidebar {docSetStats} {regionsMetadata} {docSet}/>
    </div>

    <div slot="tabs" let:activeTab>
        <div class="tabs">
            <ul>
                <li class:is-active={activeTab === 0}>
                    <a on:click={() => activeTab = 0} href="{null}">Regions Network</a>
                </li>
                <li class:is-active={activeTab === 1}>
                    <a on:click={() => activeTab = 1} href="{null}">Documents Network</a>
                </li>
            </ul>
        </div>
    </div>

    <div slot="content" let:activeTab>
        {#if $error}
            <article class="message is-danger">
                <div class="message-body">{$error}</div>
            </article>
        {:else}
            {#await fetchPairs}
                <progress class="progress is-link" max="100">Loading...</progress>
            {:then _}
                <div>
                    <h2 class="title is-3 has-text-link">{visualizationTitle}</h2>
                    <NetworkVisualization
                        networkData={activeTab === 0 ? imageNetwork : documentNetwork}
                        {selectedNodes}
                        {updateSelectedNodes}
                    />
                </div>
            {/await}
        {/if}
    </div>
</Layout>

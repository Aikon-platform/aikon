<script>
    import Layout from '../Layout.svelte';
    import Sidebar from './Sidebar.svelte';
    import NetworkVisualization from './NetworkVisualization.svelte';
    import { createDocumentSetStore } from './documentSetStore.js';

    export let docSet;

    const store = createDocumentSetStore();
    const { availableCorpora } = store;
    let activeTab = 0;

    $: availableCorpus = $availableCorpora.reduce((acc, name) => {
        acc[name] = name;
        return acc;
    }, {});

    async function handleCorpusSelect(event) {
        await store.loadCorpus(event.detail.name);
    }
</script>

<Layout bind:activeTab>
    <div slot="sidebar">
        <Sidebar
            {availableCorpus}
            selectedCorpus={$store.selectedCorpus}
            corpusStats={$store.stats}
            on:corpusSelect={handleCorpusSelect}
        />
    </div>

    <div slot="tabs" let:activeTab>
        <div class="tabs">
            <ul>
                <li class:is-active={activeTab === 0}>
                    <a on:click={() => activeTab = 0}>Regions Network</a>
                </li>
                <li class:is-active={activeTab === 1}>
                    <a on:click={() => activeTab = 1}>Documents Network</a>
                </li>
            </ul>
        </div>
    </div>

    <div slot="content" let:activeTab>
        {#if $store.loading}
            <progress class="progress is-link" max="100">Loading...</progress>
        {:else if $store.error}
            <article class="message is-danger">
                <div class="message-body">{$store.error}</div>
            </article>
        {:else if $store.data}
            {#if activeTab === 0}
                <NetworkVisualization
                    data={$store.data}
                    corpus={$store.corpus}
                    metadata={$store.metadata}
                    type="regions"
                />
            {:else}
                <NetworkVisualization
                    data={$store.data}
                    corpus={$store.corpus}
                    metadata={$store.metadata}
                    type="documents"
                />
            {/if}
        {/if}
    </div>
</Layout>

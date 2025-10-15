<script>
    import Layout from '../Layout.svelte';
    import Sidebar from './Sidebar.svelte';
    import NetworkVisualization from './NetworkVisualization.svelte';
    import { createDocumentSetStore } from './documentSetStore.js';

    export let docSet;

    const store = createDocumentSetStore();
    const { availableCorpora } = store;

    $: availableCorpus = $availableCorpora.reduce((acc, name) => {
        acc[name] = name;
        return acc;
    }, {});

    async function handleCorpusSelect(event) {
        await store.loadCorpus(event.detail.name);
    }
</script>

<Layout>
    <div slot="sidebar">
        <Sidebar
            {availableCorpus}
            selectedCorpus={$store.selectedCorpus}
            corpusStats={$store.stats}
            on:corpusSelect={handleCorpusSelect}
        />
    </div>

    <div slot="content">
        {#if $store.loading}
            <progress class="progress is-primary" max="100">Loading...</progress>
        {:else if $store.error}
            <article class="message is-danger">
                <div class="message-body">{$store.error}</div>
            </article>
        {:else if $store.data}
            <NetworkVisualization
                data={$store.data}
                corpus={$store.corpus}
                metadata={$store.metadata}
                type="regions"
            />

            <NetworkVisualization
                data={$store.data}
                corpus={$store.corpus}
                metadata={$store.metadata}
                type="documents"
            />
        {/if}
    </div>
</Layout>

<script>
    import Layout from '../Layout.svelte';
    import Sidebar from './Sidebar.svelte';
    import NetworkVisualization from './NetworkVisualization.svelte';
    import {createDocumentSetStore} from './documentSetStore.js';
    import NetworkInfo from "./NetworkInfo.svelte";
    export let docSet;

    let activeTab = 0;

    $: visualizationTitle = activeTab === 0 ? "Image regions network" : "Witness network";

    const documentSetStore = createDocumentSetStore(docSet.id);
    const { fetchPairs, error } = documentSetStore;

    /**
    import { onMount } from 'svelte';
    onMount(() => {
        const params = new URLSearchParams(window.location.search);
        const categoriesParam = params.get('categories');
        if (categoriesParam) {
            const cats = categoriesParam.split(',')
                .map(c => parseInt(c.trim()))
                .filter(c => !isNaN(c));

            if (cats.length > 0) {
                selectedCategories.set(cats);
            }
        }
    });

    $: if (typeof window !== 'undefined') {
        const url = new URL(window.location);
        url.searchParams.set('categories', $selectedCategories.join(','));
        window.history.replaceState({}, '', url);
    }
    **/
</script>

<Layout bind:activeTab>
    <div slot="sidebar">
<!--        <Sidebar {docSetStats} {regionsMetadata} {docSet} {selectedCategories} {toggleCategory} {activeRegions} {toggleRegion}>-->
        <Sidebar {docSet} {documentSetStore}>
            <div slot="datavizInfo">
                {#if activeTab === 0}
                    <p>The Regions Network visualizes the relationships between image regions across different witnesses in the document set.
                        Each node represents an image region, and edges indicate similarity or connections based on predefined criteria.</p>
                    <ul>
                        <li>Nodes: Image regions from various witnesses.</li>
                        <li>Edges: Similarity links between regions.</li>
                    </ul>
                {:else}
                    <p>The Documents Network illustrates the connections between different witnesses in the document set.
                        Each node represents a witness, and edges denote relationships based on shared content or other relevant factors.</p>
                    <ul>
                        <li>Nodes: Witnesses in the document set.</li>
                        <li>Edges: Relationships based on shared content.</li>
                    </ul>
                {/if}
                <NetworkInfo {activeTab} {documentSetStore}/>
            </div>
        </Sidebar>
    </div>

    <div slot="tabs">
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

    <div slot="content">
        {#if $error}
            <article class="message is-danger">
                <div class="message-body">{$error}</div>
            </article>
        {:else}
            {#await $fetchPairs}
                <progress class="progress is-link" max="100">Loading...</progress>
            {:then _}
                <div>
                    <h2 class="title is-3 has-text-link">{visualizationTitle}</h2>
                    <NetworkVisualization {documentSetStore} type={activeTab === 0 ? 'image' : 'document'}/>
                </div>
            {/await}
        {/if}
    </div>
</Layout>

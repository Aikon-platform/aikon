<script>
    import { appLang } from '../constants';
    import Layout from '../Layout.svelte';
    import Sidebar from './Sidebar.svelte';
    import NetworkVisualization from './NetworkVisualization.svelte';
    import DocumentMatrix from './DocumentMatrix.svelte';
    import {createDocumentSetStore} from './documentSetStore.js';
    import NetworkInfo from "./NetworkInfo.svelte";
    import {setContext} from "svelte";
    import Clusters from "./Clusters.svelte";
    export let docSet;

    let activeTab = 0;

    const documentSetStore = createDocumentSetStore(docSet.id);
    const { error, fetchPairs } = documentSetStore;

    const tabList = [
        appLang === "en" ? "Image Network" : "Réseau d'images",
        appLang === "en" ? "Document Network" : "Réseau de documents",
        appLang === "en" ? "Similarity Clusters" : "Groupe de similarités",
        appLang === "en" ? "Document Matrix" : "Matrice de documents",
    ];
    $: visualizationTitle = tabList[activeTab];

    const selectedDocuments = docSet?.selection?.selected || {
        Witness: {},
        Series: {},
        Work: {}
    };

    setContext("selectedDocuments", selectedDocuments);
    // setContext("witnessIds", Object.keys(selectedDocuments.Witness));
    // setContext("workIds", Object.keys(selectedDocuments.Work));
    // setContext("seriesIds", Object.keys(selectedDocuments.Series));

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

<Layout bind:activeTab {tabList}>
    <div slot="sidebar">
        <Sidebar {docSet} {documentSetStore}>
            <div slot="datavizInfo">
                {#if activeTab === 0}
                    <p>The Regions Network visualizes the relationships between image regions across different witnesses in the document set.
                        Each node represents an image region, and edges indicate similarity or connections based on predefined criteria.</p>
                    <ul>
                        <li>Nodes: Image regions from various witnesses.</li>
                        <li>Edges: Similarity links between regions.</li>
                    </ul>
                {:else if activeTab === 1}
                    <p>The Documents Network illustrates the connections between different witnesses in the document set.
                        Each node represents a witness, and edges denote relationships based on shared content or other relevant factors.</p>
                    <ul>
                        <li>Nodes: Witnesses in the document set.</li>
                        <li>Edges: Relationships based on shared content.</li>
                    </ul>
                {:else}
                    <p>La matrice de documents visualise les scores de similarité globaux entre tous les documents du corpus.
                        Cliquez sur une cellule pour voir les détails des similarités entre pages.</p>
                    <ul>
                        <li>Matrice : Scores normalisés entre documents (0-100).</li>
                        <li>Scatter plot : Similarités détaillées par page.</li>
                    </ul>
                {/if}
                <NetworkInfo {activeTab} {documentSetStore}/>
            </div>
        </Sidebar>
    </div>

    <div slot="content">
        {#if $error}
            <article class="message is-danger">
                <div class="message-body">{$error}</div>
            </article>
        {:else}
            {#await $fetchPairs}
                <progress class="progress is-link" max="100">Loading...</progress>
            {:then pairCount}
                {#if pairCount === 0}
                    <article class="message is-warning">
                        <div class="message-body">
                            No document pairs found for this configuration.
                            Please adjust your selection criteria in the sidebar to include more documents or categories.
                        </div>
                    </article>
                {:else}
                    <div>
                        <h2 class="title is-3 has-text-link">{visualizationTitle}</h2>
                        {#if activeTab === 0 || activeTab === 1}
                            <NetworkVisualization {documentSetStore} type={activeTab === 0 ? 'image' : 'document'}/>
                        {:else if activeTab === 2}
                            <Clusters {documentSetStore}/>
                        {:else if activeTab === 3}
                            <DocumentMatrix {documentSetStore}/>
                        {/if}
                    </div>
                {/if}
            {/await}
        {/if}
    </div>
</Layout>

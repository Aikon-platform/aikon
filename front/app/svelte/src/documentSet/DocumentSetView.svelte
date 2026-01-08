<script>
    import {onMount} from 'svelte';
    import {setContext} from "svelte";
    import {get} from 'svelte/store';

    import {appLang} from '../constants';
    import {syncStoreWithURL} from '../utils';

    import Layout from '../Layout.svelte';
    import Sidebar from './Sidebar.svelte';
    import NetworkVisualization from './NetworkVisualization.svelte';
    import DocumentMatrix from './DocumentMatrix.svelte';
    import {createDocumentSetStore} from './documentSetStore.js';
    import NetworkInfo from "./NetworkInfo.svelte";
    import Clusters from "./Clusters.svelte";
    import {createClusterStore} from "./clusterStore.js";

    export let docSet;

    const documentSetStore = createDocumentSetStore(docSet.id);
    const {error, fetchPairs, selectedRegions, selectedCategories, threshold, topK, mutualTopK, scoreMode} = documentSetStore;

    let syncRegions, syncCategories, syncThreshold, syncTopK, syncMutualTopK, syncScoreMode;
    onMount(() => {
        syncRegions = syncStoreWithURL(selectedRegions, 'regions', 'set');
        syncCategories = syncStoreWithURL(selectedCategories, 'categories', 'array');
        syncThreshold = syncStoreWithURL(threshold, 'threshold', 'number');
        syncTopK = syncStoreWithURL(topK, 'topk', 'number');
        syncMutualTopK = syncStoreWithURL(mutualTopK, 'mutual', 'boolean');
        syncScoreMode = syncStoreWithURL(scoreMode, 'mode', 'string');

        if (!get(selectedCategories)) {
            selectedCategories.set([1]);
        }

        const unsubRegions = selectedRegions.subscribe(syncRegions);
        const unsubCategories = selectedCategories.subscribe(syncCategories);
        const unsubThreshold = threshold.subscribe(syncThreshold);
        const unsubTopK = topK.subscribe(syncTopK);
        const unsubMutualTopK = mutualTopK.subscribe(syncMutualTopK);
        const unsubScoreMode = scoreMode.subscribe(syncScoreMode);

        return () => {
            unsubRegions();
            unsubCategories();
            unsubThreshold();
            unsubTopK();
            unsubMutualTopK();
            unsubScoreMode();
        };
    });

    import {clusterSelection} from '../selection/selectionStore.js';

    const {selected} = clusterSelection;
    import Modal from "../Modal.svelte";
    import {refToIIIF} from "../utils.js";

    const clusterStore = createClusterStore(documentSetStore, clusterSelection);

    const tabList = {
        "img": appLang === "en" ? "Image Network" : "Réseau d'images",
        "doc": appLang === "en" ? "Document Network" : "Réseau de documents",
        "sim": appLang === "en" ? "Copy Clusters" : "Groupe de copies",
        "mat": appLang === "en" ? "Document Matrix" : "Matrice de documents",
    };

    const selectedDocuments = docSet?.selection?.selected || {
        Witness: {},
        Series: {},
        Work: {}
    };

    setContext("selectedDocuments", selectedDocuments);
    // setContext("witnessIds", Object.keys(selectedDocuments.Witness));
    // setContext("workIds", Object.keys(selectedDocuments.Work));
    // setContext("seriesIds", Object.keys(selectedDocuments.Series));
</script>

<Layout {tabList}>
    <div slot="sidebar" let:activeTab>
        <Sidebar {docSet} {documentSetStore} {clusterStore}>
            <div slot="datavizInfo">
                {#if activeTab === "img"}
                    <p>The Regions Network visualizes the relationships between image regions across different witnesses
                        in the document set.
                        Each node represents an image region, and edges indicate similarity or connections based on
                        predefined criteria.</p>
                    <ul>
                        <li>Nodes: Image regions from various witnesses.</li>
                        <li>Edges: Similarity links between regions.</li>
                    </ul>
                {:else if activeTab === "doc"}
                    <p>The Documents Network illustrates the connections between different witnesses in the document
                        set.
                        Each node represents a witness, and edges denote relationships based on shared content or other
                        relevant factors.</p>
                    <ul>
                        <li>Nodes: Witnesses in the document set.</li>
                        <li>Edges: Relationships based on shared content.</li>
                    </ul>
                {:else}
                    <p>La matrice de documents visualise les scores de similarité globaux entre tous les documents du
                        corpus.
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

    <div slot="content" let:activeTab>

        <Modal>
            <div slot="content" class="fixed-grid has-6-cols">
                <div class="grid is-gap-2">
                    {#each Object.values(Object.values($selected)[0] || {}) as meta}
                        <div class="selection cell">
                            <figure class="image is-64x64 card">
                                <img src="{refToIIIF(meta.img, meta.xywh, '96,')}" alt="Extracted region"/>
                                <div class="overlay is-center">
                                    <span class="overlay-desc">{meta.title}</span>
                                </div>
                            </figure>
                        </div>
                    {/each}
                </div>
            </div>
        </Modal>

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
                            Please adjust your selection criteria in the sidebar to include more documents or
                            categories.
                        </div>
                    </article>
                {:else}
                    <div>
                        <h2 class="title is-3 has-text-link">{tabList[activeTab]}</h2>
                        {#if activeTab === "img" || activeTab === "doc"}
                            <NetworkVisualization {documentSetStore} type={activeTab}/>
                        {:else if activeTab === "sim"}
                            <Clusters {documentSetStore} {clusterStore}/>
                        {:else if activeTab === "mat"}
                            <DocumentMatrix {documentSetStore}/>
                        {/if}
                    </div>
                {/if}
            {/await}
        {/if}
    </div>
</Layout>

<script>
    import {onMount} from 'svelte';
    import {setContext} from "svelte";
    import { activeLayout } from '../ui/tabStore.js';

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
        syncCategories = syncStoreWithURL(selectedCategories, 'categories', 'array', [1]);
        syncThreshold = syncStoreWithURL(threshold, 'threshold', 'number');
        syncTopK = syncStoreWithURL(topK, 'topk', 'number');
        syncMutualTopK = syncStoreWithURL(mutualTopK, 'mutual', 'boolean');
        syncScoreMode = syncStoreWithURL(scoreMode, 'mode', 'string');

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
        "sim": appLang === "en" ? "Copy Clusters" : "Groupe de copies",
        "mat": appLang === "en" ? "Document Matrix" : "Matrice de documents",
        "img": appLang === "en" ? "Image Network" : "Réseau d'images",
        "doc": appLang === "en" ? "Document Network" : "Réseau de documents",
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
    <div slot="sidebar">
        <Sidebar {docSet} {documentSetStore} {clusterStore}>
            <div slot="datavizInfo">
                {#if $activeLayout === "img"}
                    <p>
                        {appLang === 'en'
                            ? 'Network where each node is an image region. Edges connect regions with similarity scores above the threshold. Node color indicates the source document.'
                            : 'Réseau où chaque nœud est une région d\'image. Les liens connectent les régions dont le score de similarité dépasse le seuil. La couleur indique le document source.'}
                    </p>
                {:else if $activeLayout === "doc"}
                    <p>
                        {appLang === 'en'
                            ? 'Network where each node is a document. Edge thickness reflects the cumulative similarity score between document pairs. Node size indicates the number of connections.'
                            : 'Réseau où chaque nœud est un document. L\'épaisseur des liens reflète le score de similarité cumulé entre paires de documents. La taille des nœuds indique le nombre de connexions.'}
                    </p>
                {:else if $activeLayout === "matrix"}
                    <p>
                        {appLang === 'en'
                            ? 'Matrix showing aggregated similarity scores between documents. Click a cell to explore page-level similarities in a scatter plot interface.'
                            : 'Matrice affichant les scores de similarité agrégés entre documents. Cliquez sur une cellule pour explorer les similarités entre paires de documents.'}
                    </p>
                {:else if $activeLayout === "clusters"}
                    <p>
                        {appLang === 'en'
                            ? 'Groups of images that share a similarity connection above the score threshold.'
                            : 'Groupes d\'images partageant une connexion de similarité au-dessus du seuil de score.'}
                    </p>
                {/if}
                <!--<NetworkInfo {$activeLayout} {documentSetStore}/>-->
            </div>
        </Sidebar>
    </div>

    <div slot="content">
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
                        <h2 class="title is-3 has-text-link">{tabList[$activeLayout]}</h2>
                        {#if $activeLayout === "img" || $activeLayout === "doc"}
                            <NetworkVisualization {documentSetStore} type={$activeLayout}/>
                        {:else if $activeLayout === "sim"}
                            <Clusters {documentSetStore} {clusterStore}/>
                        {:else if $activeLayout === "mat"}
                            <DocumentMatrix {documentSetStore}/>
                        {/if}
                    </div>
                {/if}
            {/await}
        {/if}
    </div>
</Layout>

<script>
    import {onMount} from 'svelte';
    import {setContext} from "svelte";
    import { activeLayout } from '../ui/tabStore.js';

    import {appLang} from '../constants';
    import {syncStoreWithURL} from '../utils';

    import Layout from '../Layout.svelte';
    import Sidebar from './sidebar/Sidebar.svelte';
    import NetworkVisualization from './network/NetworkVisualization.svelte';
    import DocumentMatrix from './document-matrix/DocumentMatrix.svelte';
    import {createDocumentSetStore} from './documentSetStore.js';
    import Clusters from "./clusters/Clusters.svelte";
    import {createClusterStore} from "./clusters/clusterStore.js";

    export let docSet;

    const documentSetStore = createDocumentSetStore(docSet.id);
    const {error, fetchPairs, selectedRegions, selectedCategories, threshold, topK, mutualTopK, scoreMode} = documentSetStore;

    let syncRegions, syncCategories, syncThreshold, syncTopK, syncMutualTopK, syncScoreMode;
    onMount(() => {
        syncRegions = syncStoreWithURL(selectedRegions, 'regions', 'set');
        syncCategories = syncStoreWithURL(selectedCategories, 'categories', 'array', [1]);
        // NOTE do not work with InputSlider that cannot be updated programmatically
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

    $: if ($activeLayout === 'sim') documentSetStore.setScoreFilter(true);

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
        <Sidebar {docSet} {documentSetStore} {clusterStore}/>
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

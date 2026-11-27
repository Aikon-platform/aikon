<script>
    import { run } from 'svelte/legacy';

    import {onDestroy, setContext} from "svelte";
    import { activeLayout } from "../ui/tabStore.js";

    import {appLang} from "../constants";
    import {syncStoreWithURL, msgImages} from "../utils.svelte.js";

    import Layout from "../Layout.svelte";
    import Sidebar from "./sidebar/Sidebar.svelte";
    import NetworkVisualization from "./network/NetworkVisualization.svelte";
    import DocumentMatrix from "./document-matrix/DocumentMatrix.svelte";
    import FriezeView from "./frieze/FriezeView.svelte";
    import Documents from "./documents/Documents.svelte";
    import {createDocumentSetStore} from "./documentSetStore.js";
    import Clusters from "./clusters/Clusters.svelte";
    import {createClusterStore} from "./clusters/clusterStore.js";

    import Modal from "../Modal.svelte";
    import {refToIIIF} from "../utils.svelte.js";
    import StemmaBuilder from "./stemma/StemmaBuilder.svelte";
    import {clusterSelection} from "../selection/selectionStore.js";


    let { docSet } = $props();

    const documentSetStore = createDocumentSetStore(docSet.id);
    const {error, fetchPairs, selectedDocuments, selectedCategories, threshold, topK, mutualTopK, scoreMode, docSort, hideEmpty} = documentSetStore;

    const unsubs = [
        [selectedDocuments, "doc", "set"],
        [selectedCategories, "categories", "array", [1]],
        [threshold, "threshold", "number"],
        [topK, "topk", "number"],
        [mutualTopK, "mutual", "boolean"],
        [scoreMode, "mode", "string"],
        [docSort, "sort", "string"],
        [hideEmpty, "hideEmpty", "boolean"],
    ].map(([store, ...args]) => store.subscribe(syncStoreWithURL(store, ...args)));
    onDestroy(() => unsubs.forEach(u => u()));

    const clusterStore = createClusterStore(documentSetStore, clusterSelection);

    run(() => {
        if ($activeLayout === "sim") documentSetStore.setScoreFilter(true);
    });

    const tabList = {
        "sim": appLang === "en" ? "Similarity Chains" : "Chaînes de similarité",
        "ste": appLang === "en" ? "Stemma Builder" : "Aide au stemma",
        "mat": appLang === "en" ? "Document Matrix" : "Matrice de documents",
        "fri": appLang === "en" ? "Spatial Frieze" : "Frise spatiale",
        "img": appLang === "en" ? "Image Network" : "Réseau d'images",
        "doc": appLang === "en" ? "Document Network" : "Réseau de documents",
        "wit": "Documents",
    };

    const selectedDocs = docSet?.selection?.selected || {
        Witness: {},
        Series: {},
        Work: {}
    };

    setContext("selectedDocs", selectedDocs);
</script>

<Layout {tabList}>
    {#snippet sidebar()}
        <div >
            <Sidebar {docSet} {documentSetStore} {clusterStore}/>
        </div>
    {/snippet}

    {#snippet content()}
        <div >
            <Modal>
                {#snippet content()}
                        <div  class="fixed-grid has-6-cols">
                        <div class="grid is-gap-2">
                            {#each msgImages as meta}
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
                    {/snippet}
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
                                {#if appLang === "en"}
                                    No regions pairs found for this configuration.
                                    Please adjust your selection criteria in the sidebar
                                    to include more documents or categories.
                                {:else}
                                    Aucune paires d'images trouvées pour la configuration actuelle.
                                    Merci d'ajuster vos critères de sélection dans la barre latérale
                                    pour inclure davantage de documents ou catégories.
                                {/if}
                            </div>
                        </article>
                    {:else}
                        <div>
                            <h2 class="title is-3 has-text-link">{tabList[$activeLayout]}</h2>
                            {#if $activeLayout === "img" || $activeLayout === "doc"}
                                <NetworkVisualization {documentSetStore} {clusterStore} type={$activeLayout}/>
                            {:else if $activeLayout === "sim"}
                                <Clusters {documentSetStore} {clusterStore}/>
                            {:else if $activeLayout === "mat"}
                                <DocumentMatrix {documentSetStore} {clusterStore}/>
                            {:else if $activeLayout === "ste"}
                                <StemmaBuilder {documentSetStore} {clusterStore}/>
                            {:else if $activeLayout === "fri"}
                                <FriezeView {documentSetStore} {clusterStore}/>
                            {:else if $activeLayout === "wit"}
                                <Documents {documentSetStore}/>
                            {/if}
                        </div>
                    {/if}
                {/await}
            {/if}
        </div>
    {/snippet}
</Layout>

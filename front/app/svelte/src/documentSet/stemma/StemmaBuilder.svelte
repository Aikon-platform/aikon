<script>
    import { run } from 'svelte/legacy';

    import { i18n } from "../../utils.js";
    import { parseImgRef } from "../../regions/types.js";
    import SplitLayout from "../../ui/SplitLayout.svelte";
    import DocumentSetMatrix, { viewModes } from "../document-matrix/DocumentSetMatrix.svelte";
    import DocumentPairMatrix from "../document-matrix/DocumentPairMatrix.svelte";
    import PairDetailModal from "../document-matrix/PairDetailModal.svelte";
    import { createStemmaStore } from "./stemmaStore.js";
    import SpatialFrieze from "../frieze/SpatialFrieze.svelte";
    import ImageStemma from "./ImageStemma.svelte";
    import DocumentStemmaPanel from "./DocumentStemmaPanel.svelte";
    import Matches from "../Matches.svelte";
    import DownloadPng from "../../ui/DownloadPng.svelte";

    let { documentSetStore, clusterStore } = $props();

    const {
        visiblePairs, visibleDocuments, documentNodes, imageNodes, hideEmpty,
        filteredDocPairStats, filteredDocStats, imageCountMap, coverageData, selectedDocuments, pairCat
    } = documentSetStore;

    const stemmaStore = createStemmaStore(documentSetStore);
    const {
        selectedNodes, filteredDocuments, matrixScoreData, matrixDocStats,
        matrixImageCount, getFilteredPairsForDocPair, nodeTitles,
        selectedViz, selectedCell, selectedFriezeImage, selectedCluster, matches
    } = stemmaStore;

    const t = {
        title: { en: "Document Stemma", fr: "Stemma document" },
        hint: { en: "Right click to edit • Scroll to zoom • Shift+drag to connect", fr: "Clic droit pour modifier • Défiler pour zoomer • Maj+glisser pour connecter" },
        order: { en: "Order", fr: "Ordre" },
        edges: { en: "Connections", fr: "Connexions" },
        normalize: {en: "Normalize", fr: "Normaliser"},
        normalization: {en: "Normalization by document image counts", fr: "Normalisation par le nombre d'images des documents"},
        imageStemma: {en: "Image stemma from", fr: "Stemma d'images issu de"},
        noSelection: { en: "Connect documents in the stemma to see visualizations", fr: "Connectez des documents dans le stemma pour voir les visualisations" },
        noViz: { en: "Select a visualization above", fr: "Sélectionnez une visualisation ci-dessus" },
        byPage: { en: "By page", fr: "Par page" },
        byImage: { en: "By image", fr: "Par image" },
        selectedDocs: { en: "Selected documents", fr: "Documents sélectionnés" },
        fullDocSet: { en: "Full document set", fr: "Jeu de documents complet" },
        viewMode: {en: "Matrix display mode", fr: "Mode d'affichage de la matrice"},
        matches: {en: "Matches", fr: "Correspondances"},

        selectViz: { en: "Select a visualization", fr: "Choisir une visualisation" },
        docMatrix: { en: "Document Matrix", fr: "Matrice de documents" },
        spatialFrieze: { en: "Spatial Frieze", fr: "Frise spatiale" },
    };

    const vizOptions = [
        { id: "spatialFrieze", label: t.spatialFrieze },
        { id: "docMatrix", label: t.docMatrix },
    ];

    const layouts = {
        "":              { left: "documentStemma", right: null,     bottomRight: "pair",           bottomLeft: null },
        "docMatrix":     { left: "documentStemma", right: "matrix", bottomRight: "pair",           bottomLeft: "matches" },
        "spatialFrieze": { left: "imageStemma",    right: "frieze", bottomRight: "documentStemma", bottomLeft: "matches" },
    };
    let layout = $derived(layouts[$selectedViz] ?? layouts[""]);

    let scatterMode = $state("image");
    let friezeMode = $state("image");
    let viewMode = $state("matches");
    let modalActive = $state(false);
    let navState = $state(null);
    let scatterData = $state(null);
    let matrixScope = $state("full");

    run(() => {
        documentSetStore.updateSelectedNodes($selectedNodes.map(n => n.id));
    });
    let pairMatrixData = $derived($selectedCell ? {
        doc1: $selectedCell.doc1,
        doc2: $selectedCell.doc2,
        pairs: getFilteredPairsForDocPair($selectedCell.doc1.id, $selectedCell.doc2.id)
    } : null);

    function handleScatterClick(e) {
        navState = { idx1: e.detail.idx1, idx2: e.detail.idx2 };
        scatterData = e.detail.data;
        modalActive = true;
    }
    function handleModalNavigate(e) { navState = { ...e.detail }; }
    function handleModalClose() { modalActive = false; }

    let fullDocuments = $derived($visibleDocuments);
    let fullScoreData = $derived($filteredDocPairStats?.scoreCount || new Map());
    let fullDocStats = $derived($filteredDocStats?.scoreCount || new Map());
    let friezeDocuments = $derived((() => {
        if (matrixScope === "full") return fullDocuments;
        const anchorDoc = $documentNodes.get($selectedFriezeImage?.baseDocId);
        const base = anchorDoc ? [...$selectedNodes, anchorDoc] : $selectedNodes;
        return base.filter(d => $selectedDocuments.has(d.id));
    })());
    let needsSelection = $derived($selectedViz && !$selectedNodes.length && matrixScope !== "full");
    run(() => {
        if (matrixScope) selectedCluster.set(null);
    });
</script>

<SplitLayout>
    <!-- @migration-task-ok: migrate this slot by hand, `left-title` is an invalid identifier -->
    {#snippet leftTitle()}
        <div id="stemma-header" class="is-flex is-justify-content-space-between is-align-items-center">
            {#if layout.left === "documentStemma"}
                <h4 class="title is-6 mb-0 mr-3 panel-title">{i18n("title", t)}</h4>
                <div class="is-flex is-align-items-center">
                    <DownloadPng targetId="doc-stemma" filename="document-stemma" svgExport={true}/>
                    <span class="tag is-small ml-3">{i18n("hint", t)}</span>
                </div>
            {:else if layout.left === "imageStemma" && $selectedFriezeImage}
                {@const baseDoc = $selectedNodes.find(d => d.id === $selectedFriezeImage.baseDocId)}
                {@const title = $nodeTitles[$selectedFriezeImage.baseDocId] || baseDoc?.title}
                {@const imgData = parseImgRef($selectedFriezeImage.imageId)}
                <h4 class="title is-6 mb-0 px-2 panel-title">
                    Page {imgData?.canvasNb || 0}
                    <span class="color-dot" style="background: {baseDoc?.color}"></span>
                    {title ?? "Unknown"}
                </h4>
                <div class="is-flex is-align-items-center">
                    <DownloadPng targetId="img-stemma" filename="image-stemma" svgExport={true}/>
                    <span class="tag is-small ml-3">{i18n("hint", t)}</span>
                </div>
            {/if}
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `left-scroll` is an invalid identifier -->
    {#snippet leftScroll()}
        <div>
            {#if layout.left === "documentStemma"}
                <DocumentStemmaPanel
                    {stemmaStore}
                    documents={$filteredDocuments}
                    selectedNodes={$selectedNodes}
                    nodeTitles={$nodeTitles}/>
            {:else if layout.left === "imageStemma"}
                <ImageStemma
                    {stemmaStore} {visiblePairs} {imageNodes}
                    documents={friezeDocuments}
                    startImageId={$selectedFriezeImage?.imageId ?? null}
                    baseDocId={$selectedFriezeImage?.baseDocId ?? null}
                    on:anchorselect={e => selectedFriezeImage.set(e.detail)}
                />
            {/if}
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `bottom-left-title` is an invalid identifier -->
    {#snippet bottomLeftTitle()}
        <div class="is-flex is-justify-content-space-between">
            {#if layout.bottomLeft === "matches" && $matches.matches.length}
                <h4 class="title is-6 mb-0">
                    {i18n("matches", t)} ({$matches.matches.length})
                </h4>
            {/if}
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `bottom-left-scroll` is an invalid identifier -->
    {#snippet bottomLeftScroll()}
        <div>
            {#if layout.bottomLeft === "matches"}
                <Matches matches={$matches.matches} columns={$matches.columns} isInStemma={$selectedViz === "spatialFrieze"}
                         pairCat={$pairCat} {clusterStore} on:anchorselect={e => selectedFriezeImage.set(e.detail)}/>
            {/if}
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `right-title` is an invalid identifier -->
    {#snippet rightTitle()}
        <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
            <div class="select is-small">
                <select bind:value={$selectedViz}>
                    <option value="">{i18n("selectViz", t)}</option>
                    {#each vizOptions as opt}
                        <option value={opt.id}>{i18n(opt.id, t)}</option>
                    {/each}
                </select>
            </div>
            {#if $selectedViz}
                <DownloadPng targetId={$selectedViz === "spatialFrieze" ? "spatial-frieze" : "doc-set-matrix"} filename={$selectedViz} svgExport={true}/>
                <div class="select is-small">
                    <select bind:value={matrixScope}>
                        <option value="selected">{i18n("selectedDocs", t)}</option>
                        <option value="full">{i18n("fullDocSet", t)}</option>
                    </select>
                </div>
            {/if}
            {#if $selectedViz === "docMatrix"}
    <!--            <label title={i18n("normalization", t)} class="checkbox is-size-7 is-flex is-align-items-center">-->
    <!--                <input type="checkbox" bind:checked={$normalizeByImages}>-->
    <!--                <span class="pl-1">{i18n("normalize", t)}</span>-->
    <!--            </label>-->
                <div class="select is-small" title={i18n("viewMode", t)}>
                    <select bind:value={viewMode}>
                        {#each Object.keys(viewModes) as m}
                            <option value={m}>{i18n(m, viewModes)}</option>
                        {/each}
                    </select>
                </div>
            {:else if $selectedViz === "spatialFrieze"}
                <div class="select is-small">
                    <select bind:value={friezeMode}>
                        <option value="page">{i18n("byPage", t)}</option>
                        <option value="image">{i18n("byImage", t)}</option>
                    </select>
                </div>
            {/if}
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `right-scroll` is an invalid identifier -->
    {#snippet rightScroll()}
        <div>
            {#if !$selectedViz}
                <p class="has-text-grey is-size-7">{i18n("noViz", t)}</p>
            {:else if needsSelection}
                <p class="has-text-grey is-size-7">{i18n("noSelection", t)}</p>
            {:else if layout.right === "matrix"}
                <DocumentSetMatrix
                    documents={matrixScope === "full" ? fullDocuments : $selectedNodes}
                    scoreData={matrixScope === "full" ? fullScoreData : $matrixScoreData}
                    docStats={matrixScope === "full" ? fullDocStats : $matrixDocStats}
                    imageCountMap={matrixScope === "full" ? $imageCountMap : $matrixImageCount}
                    mode={viewMode}
                    {coverageData}
                    isInStemma={true} {stemmaStore}
                    on:cellselect={e => selectedCell.set(e.detail)}
                />
            {:else if layout.right === "frieze"}
                <SpatialFrieze
                    documents={friezeDocuments}
                    {visiblePairs}
                    {documentNodes}
                    isInStemma={true} {stemmaStore}
                    mode={friezeMode}
                    on:imageselect={e => { selectedFriezeImage.set(e.detail); selectedCluster.set(null); }}
                    on:clusterselect={e => { selectedCluster.set(e.detail); selectedFriezeImage.set(null); }}
                />
            {/if}
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `bottom-right-title` is an invalid identifier -->
    {#snippet bottomRightTitle()}
        <div class="is-flex is-justify-content-space-between is-align-items-center">
            {#if layout.bottomRight === "pair" && pairMatrixData}
                <div class="is-flex is-align-items-center">
                    <h4 class="title is-6 mb-0 mr-3">
                        <span class="color-dot" style="background: {pairMatrixData.doc1.color}"></span>
                        <span class="has-text-grey">↔</span>
                        <span class="color-dot" style="background: {pairMatrixData.doc2.color}"></span>
                    </h4>
                    <DownloadPng targetId="doc-pair-matrix" filename="doc-pair-matrix" svgExport={true}/>
                </div>

                <div class="select is-small ml-3">
                    <select bind:value={scatterMode}>
                        <option value="page">{i18n("byPage", t)}</option>
                        <option value="image">{i18n("byImage", t)}</option>
                    </select>
                </div>
            {:else if layout.bottomRight === "documentStemma"}
                <h4 class="title is-6 mb-0 mr-3 panel-title">{i18n("title", t)}</h4>
                <div class="is-flex is-align-items-center">
                    <DownloadPng targetId="doc-stemma" filename="document-stemma"  svgExport={true}/>
                    <span class="tag is-small ml-3">{i18n("hint", t)}</span>
                </div>
            {/if}
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `bottom-right-scroll` is an invalid identifier -->
    {#snippet bottomRightScroll()}
        <div>
            {#if layout.bottomRight === "pair" && pairMatrixData}
                <DocumentPairMatrix
                    doc1={pairMatrixData.doc1}
                    doc2={pairMatrixData.doc2}
                    pairs={pairMatrixData.pairs}
                    mode={scatterMode}
                    hideEmpty={$hideEmpty}
                    on:cellclick={handleScatterClick}
                />
            {:else if layout.bottomRight === "documentStemma"}
                <DocumentStemmaPanel
                    {stemmaStore}
                    documents={$filteredDocuments}
                    selectedNodes={$selectedNodes}
                    nodeTitles={$nodeTitles}/>
            {/if}
        </div>
    {/snippet}
</SplitLayout>

<PairDetailModal {documentSetStore}
    active={modalActive} {scatterData} {navState} pairCat={$pairCat}
    on:navigate={handleModalNavigate}
    on:close={handleModalClose}
/>

<style>
    #stemma-header {
        overflow: hidden;
        white-space: nowrap;
    }
    .color-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .panel-title {
        max-width: 80%;
        text-overflow: ellipsis;
        overflow: hidden;
        max-height: 1em;
    }
</style>

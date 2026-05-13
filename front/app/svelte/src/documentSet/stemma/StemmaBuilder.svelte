<script>
    import { i18n } from "../../utils.js";
    import { parseImgRef } from "../../regions/types.js";
    import SplitLayout from "../../ui/SplitLayout.svelte";
    import DocumentSetMatrix from "../document-matrix/DocumentSetMatrix.svelte";
    import DocumentPairMatrix from "../document-matrix/DocumentPairMatrix.svelte";
    import PairDetailModal from "../document-matrix/PairDetailModal.svelte";
    import { createStemmaStore } from "./stemmaStore.js";
    import SpatialFrieze from "../frieze/SpatialFrieze.svelte";
    import ImageStemma from "./ImageStemma.svelte";
    import DocumentStemmaPanel from "./DocumentStemmaPanel.svelte";
    import Matches from "../Matches.svelte";
    import DownloadPng from "../../ui/DownloadPng.svelte";

    export let documentSetStore;

    const {
        normalizeByImages, visiblePairs, documentNodes, imageNodes,
        filteredDocPairStats, filteredDocStats, imageCountMap, coverageData
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
        percentage: {en: "By percentage", fr: "Par pourcentage"},
        percentageView: {en: "View matrix with image similarity percentage", fr: "Visualiser la matrice avec des pourcentage d'images similaires"},
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
    $: layout = layouts[$selectedViz] ?? layouts[""];

    let scatterMode = "image";
    let friezeMode = "image";
    let percentageMode = false;
    let modalActive = false;
    let navState = null;
    let scatterData = null;
    let matrixScope = "full";

    $: documentSetStore.updateSelectedNodes($selectedNodes.map(n => n.id));
    $: pairMatrixData = $selectedCell ? {
        doc1: $selectedCell.doc1,
        doc2: $selectedCell.doc2,
        pairs: getFilteredPairsForDocPair($selectedCell.doc1.id, $selectedCell.doc2.id)
    } : null;

    function handleScatterClick(e) {
        navState = { idx1: e.detail.idx1, idx2: e.detail.idx2 };
        scatterData = e.detail.data;
        modalActive = true;
    }
    function handleModalNavigate(e) { navState = { ...e.detail }; }
    function handleModalClose() { modalActive = false; }

    $: fullDocuments = Array.from($documentNodes?.values() || []);
    $: fullScoreData = $filteredDocPairStats?.scoreCount || new Map();
    $: fullDocStats = $filteredDocStats?.scoreCount || new Map();
    // $: friezeDocuments = matrixScope === "full" ? fullDocuments : $selectedNodes;
    $: friezeDocuments = (() => {
        if (matrixScope === "full") return fullDocuments;
        const anchorDoc = $documentNodes?.get($selectedFriezeImage?.baseDocId);
        return anchorDoc ? [...$selectedNodes, anchorDoc] : $selectedNodes;
    })();
    $: needsSelection = $selectedViz && !$selectedNodes.length && matrixScope !== "full";
    $: if (matrixScope) selectedCluster.set(null);
</script>

<SplitLayout>
    <div id="stemma-header" slot="left-title" class="is-flex is-justify-content-space-between is-align-items-center">
        {#if layout.left === "documentStemma"}
            <div class="is-flex is-align-items-center">
                <h4 class="title is-6 mb-0 mr-3">{i18n("title", t)}</h4>
                <DownloadPng targetId="doc-stemma" filename="document-stemma.png" />
            </div>
        {:else if layout.left === "imageStemma" && $selectedFriezeImage}
            {@const baseDoc = $selectedNodes.find(d => d.id === $selectedFriezeImage.baseDocId)}
            {@const title = $nodeTitles[$selectedFriezeImage.baseDocId] || baseDoc?.title}
            {@const imgData = parseImgRef($selectedFriezeImage.imageId)}
            <h4 class="title is-6 mb-0 px-2" style="max-width: 80%; text-overflow: ellipsis; overflow: hidden">
                <!--<span>{i18n("imageStemma", t)}</span>-->
                Page {imgData?.canvasNb || 0}
                <span class="color-dot" style="background: {baseDoc?.color}"/>
                {title ?? "Unknown"}
            </h4>
            <DownloadPng targetId="img-stemma" filename="image-stemma.png" />
        {/if}
        <span class="tag is-small ml-3">{i18n("hint", t)}</span>
    </div>

    <div slot="left-scroll">
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

    <div slot="bottom-left-title" class="is-flex is-justify-content-space-between">
        {#if layout.bottomLeft === "matches" && $matches.matches.length}
            <h4 class="title is-6 mb-0">
                {i18n("matches", t)} ({$matches.matches.length})
            </h4>
        {/if}
    </div>
    <div slot="bottom-left-scroll">
        {#if layout.bottomLeft === "matches"}
            <Matches matches={$matches.matches} columns={$matches.columns} isInStemma={$selectedViz === "spatialFrieze"}
                     on:anchorselect={e => selectedFriezeImage.set(e.detail)}/>
        {/if}
    </div>

    <div slot="right-title" class="is-flex is-align-items-center" style="gap: 0.5rem;">
        <div class="select is-small">
            <select bind:value={$selectedViz}>
                <option value="">{i18n("selectViz", t)}</option>
                {#each vizOptions as opt}
                    <option value={opt.id}>{i18n(opt.id, t)}</option>
                {/each}
            </select>
        </div>
        {#if $selectedViz}
            <DownloadPng targetId={$selectedViz === "spatialFrieze" ? "spatial-frieze" : "doc-set-matrix"} filename={`${$selectedViz}.png`} />
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
            <label title={i18n("percentageView", t)} class="checkbox is-size-7 is-flex is-align-items-center">
                <input type="checkbox" bind:checked={percentageMode}>
                <span class="pl-1">{i18n("percentage", t)}</span>
            </label>
        {:else if $selectedViz === "spatialFrieze"}
            <div class="select is-small">
                <select bind:value={friezeMode}>
                    <option value="page">{i18n("byPage", t)}</option>
                    <option value="image">{i18n("byImage", t)}</option>
                </select>
            </div>
        {/if}
    </div>

    <div slot="right-scroll">
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
                normalize={!percentageMode}
                {percentageMode}
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

    <div slot="bottom-right-title" class="is-flex is-justify-content-space-between">
        {#if layout.bottomRight === "pair" && pairMatrixData}
            <div class="is-flex is-align-items-center">
                <h4 class="title is-6 mb-0 mr-3">
                    <span class="color-dot" style="background: {pairMatrixData.doc1.color}"/>
                    <span class="has-text-grey">↔</span>
                    <span class="color-dot" style="background: {pairMatrixData.doc2.color}"/>
                </h4>
                <DownloadPng targetId="doc-pair-matrix" filename="doc-pair-matrix.png" />
            </div>

            <div class="select is-small ml-3">
                <select bind:value={scatterMode}>
                    <option value="page">{i18n("byPage", t)}</option>
                    <option value="image">{i18n("byImage", t)}</option>
                </select>
            </div>
        {:else if layout.bottomRight === "documentStemma"}
            <div class="is-flex is-align-items-center">
                <h4 class="title is-6 mb-0 mr-3">{i18n("title", t)}</h4>
                <DownloadPng targetId="doc-stemma" filename="document-stemma.png" />
            </div>
            <span class="tag is-small ml-3">{i18n("hint", t)}</span>
        {/if}

    </div>

    <div slot="bottom-right-scroll">
        {#if layout.bottomRight === "pair" && pairMatrixData}
            <DocumentPairMatrix
                doc1={pairMatrixData.doc1}
                doc2={pairMatrixData.doc2}
                pairs={pairMatrixData.pairs}
                mode={scatterMode}
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
</SplitLayout>

<PairDetailModal
    active={modalActive} {scatterData} {navState}
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
</style>

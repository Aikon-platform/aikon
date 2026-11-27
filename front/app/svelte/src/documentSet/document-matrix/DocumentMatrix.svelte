<script>
    import { run } from 'svelte/legacy';

    import {i18n} from "../../utils.svelte.js";
    import DownloadPng from "../../ui/DownloadPng.svelte";
    import SplitLayout from "../../ui/SplitLayout.svelte";
    import DocumentSetMatrix, {viewModes} from "./DocumentSetMatrix.svelte";
    import DocumentPairMatrix from "./DocumentPairMatrix.svelte";
    import PairDetailModal from "./PairDetailModal.svelte";
    import Matches from "../Matches.svelte";

    let { documentSetStore, clusterStore } = $props();

    const {
        visibleDocuments, getFilteredPairsForDocPair, filteredDocPairStats, filteredDocStats,
        imageCountMap, visiblePairIds, coverageData, buildMatchesForAnchor, hideEmpty, pairCat
    } = documentSetStore;

    const t = {
        title: {en: "Document Matrix", fr: "Matrice de documents"},
        byName: {en: "By title", fr: "Par titre"},
        byScore: {en: "By score", fr: "Par score"},
        pageByPage: {en: "Page-by-page similarity", fr: "Similarité page par page"},
        selectCell: {en: "Click a cell to view page-by-page similarity", fr: "Cliquez sur une cellule pour voir la similarité page par page"},
        byPage: {en: "By page", fr: "Par page"},
        byImage: {en: "By image", fr: "Par image"},
        normalize: {en: "Normalize", fr: "Normaliser"},
        normalization: {en: "Normalization by document image counts", fr: "Normalisation par le nombre d'images des documents"},
        percentage: {en: "By percentage", fr: "Par pourcentage"},
        percentageView: {en: "View matrix with image similarity percentage", fr: "Visualiser la matrice avec des pourcentage d'images similaires"},
        allPairs: {en: "All pairs in the document set", fr: "Toutes les paires du corpus"},
        filteredPairs: {en: "Filtered pairs", fr: "Paires après filtrage"},
        filtering: {en: "Source of image pairs for the visualizations", fr: "Source des paires d'images pour les visualisations"},
        matches: {en: "Matches", fr: "Correspondances"},
        viewMode: {en: "Matrix display mode", fr: "Mode d'affichage de la matrice"},
    };

    let selectedCell = $state(null);
    let sortOrder = "name";
    let scatterMode = $state("image");
    let navState = $state(null);
    let modalActive = $state(false);
    let scatterData = $state(null);
    let viewMode = $state("matches");

    let documents = $derived($visibleDocuments);
    run(() => {
        if (selectedCell && [selectedCell.doc1, selectedCell.doc2].some(d => !documents.some(v => v.id === d.id))) selectedCell = null;
    });

    let pairsForSelection = $derived(selectedCell ? ($visiblePairIds, getFilteredPairsForDocPair(selectedCell.doc1.id, selectedCell.doc2.id)) : []);
    let matchesData = $derived(selectedCell
        ? buildMatchesForAnchor(selectedCell.doc1, [selectedCell.doc2], null, false, true)
        : { matches: [], columns: [] });

    function handleCellSelect(e) {
        selectedCell = e.detail;
    }

    function handleScatterClick(e) {
        navState = {idx1: e.detail.idx1, idx2: e.detail.idx2};
        scatterData = e.detail.data;
        modalActive = true;
    }

    function handleModalNavigate(e) {
        navState = {...e.detail};
    }

    function handleModalClose() {
        modalActive = false;
    }
</script>

<SplitLayout>
    <!-- @migration-task-ok: migrate this slot by hand, `left-title` is an invalid identifier -->
    {#snippet leftTitle()}
        <div class="is-flex is-justify-content-space-between">
            <h4 class="title is-6 mb-0">{i18n("title", t)}</h4>
            <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
                <DownloadPng targetId="matrix-viz" filename="document-matrix" svgExport={true}/>
                <div class="select is-small" title={i18n("viewMode", t)}>
                    <select bind:value={viewMode}>
                        {#each Object.keys(viewModes) as m}
                            <option value={m}>{i18n(m, viewModes)}</option>
                        {/each}
                    </select>
                </div>
            </div>
        </div>
    {/snippet}
    <!-- @migration-task-ok: migrate this slot by hand, `left-scroll` is an invalid identifier -->
    {#snippet leftScroll()}
        <div id="matrix-viz">
            <DocumentSetMatrix
                {documents} {sortOrder}
                scoreData={$filteredDocPairStats.scoreCount}
                docStats={$filteredDocStats.scoreCount}
                imageCountMap={$imageCountMap}
                mode={viewMode}
                on:cellselect={handleCellSelect}
                {coverageData}
            />
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `bottom-left-title` is an invalid identifier -->
    {#snippet bottomLeftTitle()}
        <div slot="bottom-left-title" class="is-flex is-justify-content-space-between">
            {#if matchesData.matches.length}
                <h4 class="title is-6 mb-0">
                    {i18n("matches", t)} ({matchesData.matches.length})
                </h4>
            {/if}
        </div>
    {/snippet}
    <!-- @migration-task-ok: migrate this slot by hand, `bottom-left-scroll` is an invalid identifier -->
    {#snippet bottonLeftScroll()}
        <div>
            <Matches matches={matchesData.matches} columns={matchesData.columns} hideEmpty={$hideEmpty} pairCat={$pairCat} {clusterStore}/>
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `right-title` is an invalid identifier -->
    {#snippet rightTitle()}
        <div class="is-flex is-justify-content-space-between">
            <h4 class="title is-6 mb-0">{i18n("pageByPage", t)}</h4>
            <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
                {#if selectedCell}
                    <DownloadPng targetId="scatter-viz" filename="document-comparison" svgExport={true}/>
                    <div class="control">
                        <div class="select is-small">
                            <select bind:value={scatterMode}>
                                <option value="page">{i18n("byPage", t)}</option>
                                <option value="image">{i18n("byImage", t)}</option>
                            </select>
                        </div>
                    </div>
                {/if}
            </div>
        </div>
    {/snippet}
    <!-- @migration-task-ok: migrate this slot by hand, `right-scroll` is an invalid identifier -->
    {#snippet rightScroll()}
        <div id="scatter-viz">
            {#if selectedCell}
                <DocumentPairMatrix
                    doc1={selectedCell.doc1}
                    doc2={selectedCell.doc2}
                    pairs={pairsForSelection}
                    mode={scatterMode}
                    hideEmpty={$hideEmpty}
                    on:cellclick={handleScatterClick}
                />
            {:else}
                <p class="has-text-grey is-size-7">{i18n("selectCell", t)}</p>
            {/if}
        </div>
    {/snippet}
</SplitLayout>

<PairDetailModal {documentSetStore}
    active={modalActive} {scatterData} {navState} pairCat={$pairCat}
    on:navigate={handleModalNavigate}
    on:close={handleModalClose}
/>

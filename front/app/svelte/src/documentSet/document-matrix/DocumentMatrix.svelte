<script>
    import {appLang} from '../../constants.js';
    import DownloadPng from "../../ui/DownloadPng.svelte";
    import SplitLayout from "../../ui/SplitLayout.svelte";
    import SetMatrix from "./SetMatrix.svelte";
    import DocumentPairMatrix from "./DocumentPairMatrix.svelte";
    import PairDetailModal from "./PairDetailModal.svelte";

    export let documentSetStore;

    const {
        documentNodes, pairIndex, activeDocPairStats, activeDocStats,
        imageCountMap, visiblePairIds, matrixMode, normalizeByImages
    } = documentSetStore;

    const t = {
        title: {en: 'Document Matrix', fr: 'Matrice de documents'},
        byName: {en: 'By title', fr: 'Par titre'},
        byScore: {en: 'By score', fr: 'Par score'},
        noDocuments: {en: 'No documents available', fr: 'Aucun document disponible'},
        pageByPage: {en: 'Page-by-page similarity', fr: 'Similarité page par page'},
        selectCell: {en: 'Click a cell to view page-by-page similarity', fr: 'Cliquez sur une cellule pour voir la similarité page par page'},
        byPage: {en: 'By page', fr: 'Par page'},
        byImage: {en: 'By image', fr: 'Par image'},
        normalize: {en: 'Normalize', fr: 'Normaliser'},
        normalization: {en: 'Normalization by document image counts', fr: "Normalisation par le nombre d'images des documents"},
        allPairs: {en: 'All pairs in the document set', fr: 'Toutes les paires du corpus'},
        filteredPairs: {en: 'Filtered pairs', fr: 'Paires après filtrage'},
        filtering: {en: 'Source of image pairs for the visualizations', fr: "Source des paires d'images pour les visualisations"},
    };
    const i18n = (key) => t[key]?.[appLang] || t[key]?.en || key;

    let selectedCell = null;
    let sortOrder = 'name';
    let scatterMode = 'page';
    let navState = null;
    let modalActive = false;
    let pairMatrixRef;

    $: documents = Array.from($documentNodes?.values() || []);
    $: pairsForSelection = selectedCell ? getPairsForCell(selectedCell, $matrixMode === 'filtered', $visiblePairIds) : [];

    function getPairsForCell(cell, filterPairs, visibleIds) {
        const {doc1, doc2} = cell;
        const pairKey = doc1.id < doc2.id ? `${doc1.id}-${doc2.id}` : `${doc2.id}-${doc1.id}`;
        let pairs = $pairIndex.byDocPair.get(pairKey) || [];
        if (filterPairs && visibleIds.size > 0) pairs = pairs.filter(p => visibleIds.has(`${p.id_1}-${p.id_2}`));
        return pairs;
    }

    function handleCellSelect(e) {
        selectedCell = e.detail;
    }

    function handleScatterClick(e) {
        navState = {idx1: e.detail.idx1, idx2: e.detail.idx2};
        modalActive = true;
    }

    function handleModalNavigate(e) {
        navState = {...e.detail};
    }

    function handleModalClose() {
        modalActive = false;
    }
</script>

<div class="field mb-4">
    <label class="label is-small" for="matrix-mode">{i18n('filtering')}</label>
    <div class="control">
        <div class="select is-small is-fullwidth">
            <select id="matrix-mode" bind:value={$matrixMode}>
                <option value="all">{i18n('allPairs')}</option>
                <option value="filtered">{i18n('filteredPairs')}</option>
            </select>
        </div>
    </div>
</div>

{#if !documents.length}
    <div class="container">
        <div class="notification is-info" style="width: 100%">{i18n('noDocuments')}</div>
    </div>
{:else}
    <SplitLayout>
        <div slot="left-title" class="is-flex is-justify-content-space-between">
            <h4 class="title is-6 mb-0">{i18n('title')}</h4>
            <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
                <DownloadPng targetId="matrix-viz" filename="document-matrix.png" />
                <div class="control">
                    <div class="select is-small">
                        <select bind:value={sortOrder}>
                            <option value="name">{i18n('byName')}</option>
                            <option value="score">{i18n('byScore')}</option>
                        </select>
                    </div>
                </div>
                <label title={i18n('normalization')} class="checkbox is-size-7">
                    <input type="checkbox" checked={$normalizeByImages} on:change={e => normalizeByImages.set(e.target.checked)}>
                    {i18n('normalize')}
                </label>
            </div>
        </div>
        <div slot="left-scroll" id="matrix-viz">
            <SetMatrix
                {documents} {sortOrder}
                scoreData={$activeDocPairStats.scoreCount}
                docStats={$activeDocStats.scoreCount}
                imageCountMap={$imageCountMap}
                normalize={$normalizeByImages}
                on:cellselect={handleCellSelect}
            />
        </div>
        <div slot="right-title" class="is-flex is-justify-content-space-between">
            <h4 class="title is-6 mb-0">{i18n('pageByPage')}</h4>
            <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
                {#if selectedCell}
                    <DownloadPng targetId="scatter-viz" filename="document-comparison.png"/>
                    <div class="control">
                        <div class="select is-small">
                            <select bind:value={scatterMode}>
                                <option value="page">{i18n('byPage')}</option>
                                <option value="image">{i18n('byImage')}</option>
                            </select>
                        </div>
                    </div>
                {/if}
            </div>
        </div>
        <div slot="right-scroll" id="scatter-viz">
            {#if selectedCell}
                <DocumentPairMatrix
                    bind:this={pairMatrixRef}
                    doc1={selectedCell.doc1}
                    doc2={selectedCell.doc2}
                    pairs={pairsForSelection}
                    mode={scatterMode}
                    on:cellclick={handleScatterClick}
                />
            {:else}
                <p class="has-text-grey is-size-7">{i18n('selectCell')}</p>
            {/if}
        </div>
    </SplitLayout>
{/if}

<PairDetailModal
    active={modalActive}
    scatterData={pairMatrixRef?.getScatterData()}
    {navState}
    on:navigate={handleModalNavigate}
    on:close={handleModalClose}
/>

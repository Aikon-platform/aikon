<script>
    import * as d3 from 'd3';
    import {appLang} from '../constants.js';
    import {onMount, onDestroy} from 'svelte';
    import {closeModal, refToIIIF} from '../utils.js';

    export let documentSetStore;

    const {documentNodes, docPairStats, pairIndex, documentStats} = documentSetStore;

    const t = {
        title: {en: 'Document Matrix', fr: 'Matrice de documents'},
        order: {en: 'Order', fr: 'Ordre'},
        byName: {en: 'By name', fr: 'Par nom'},
        byScore: {en: 'By score', fr: 'Par score'},
        noDocuments: {en: 'No documents available', fr: 'Aucun document disponible'},
        pageByPage: {en: 'Page-by-page similarity', fr: 'Similarité page par page'},
        page: {en: 'page', fr: 'page'},
        score: {en: 'Score', fr: 'Score'},
        noPairs: {en: 'No pairs', fr: 'Aucune paire'},
        selectCell: {
            en: 'Click a cell to view page-by-page similarity',
            fr: 'Cliquez sur une cellule pour voir la similarité page par page'
        }
    };
    const i18n = (key) => t[key]?.[appLang] || t[key]?.en || key;

    let container;
    let matrixContainer;
    let scatterContainer;
    let modalElement;
    let selectedCell = null;
    let sortOrder = 'name';
    let splitRatio = 0.5;
    let isDragging = false;
    let containerWidth = 0;
    let resizeObserver;

    let clickedPage = null;

    const MIN_WIDTH = 300;

    $: documents = Array.from($documentNodes?.values() || []);
    $: matrixData = buildMatrix(documents, $docPairStats.scoreCount, $documentStats.scoreCount, sortOrder);
    $: scatterData = selectedCell ? buildScatter(selectedCell) : null;
    $: leftWidth = Math.max(MIN_WIDTH, containerWidth * splitRatio - 4);
    $: rightWidth = Math.max(MIN_WIDTH, containerWidth * (1 - splitRatio) - 4);

    const cellSize = 30;
    const scatterCellSize = 5;

    function buildMatrix(docs, scoreCount, docStats, order) {
        if (!docs.length) return {docs: [], matrix: [], maxScore: 0};

        docs.forEach((doc, i) => {
            doc.index = i;
            doc.count = docStats?.get(doc.id)?.count || 0;
        });

        const orders = {
            name: d3.range(docs.length).sort((a, b) => docs[a].title.localeCompare(docs[b].title)),
            score: d3.range(docs.length).sort((a, b) => docs[b].count - docs[a].count),
        };

        const sorted = orders[order].map(i => docs[i]);
        const n = sorted.length;
        const matrix = [];
        let maxScore = 0;

        for (let i = 0; i < n; i++) {
            const row = [];
            for (let j = 0; j < n; j++) {
                if (i !== j) {
                    const key = sorted[i].id < sorted[j].id
                        ? `${sorted[i].id}-${sorted[j].id}`
                        : `${sorted[j].id}-${sorted[i].id}`;
                    const score = scoreCount?.get(key)?.score || 0;
                    if (score > maxScore) maxScore = score;
                    row.push({x: j, y: i, z: score, doc1: sorted[i], doc2: sorted[j]});
                } else {
                    row.push({x: j, y: i, z: 0, diagonal: true});
                }
            }
            matrix.push(row);
        }

        return {docs: sorted, matrix, maxScore};
    }

    function buildScatter(cell) {
        const {doc1, doc2} = cell;
        const pairKey = doc1.id < doc2.id ? `${doc1.id}-${doc2.id}` : `${doc2.id}-${doc1.id}`;
        const pairs = $pairIndex.byDocPair.get(pairKey) || [];

        if (!pairs.length) return null;

        const pageMap = new Map();
        let minScore = Infinity, maxScore = -Infinity;

        pairs.forEach(p => {
            const [page1, page2, score] = p.regions_id_1 === doc1.id
                ? [p.page_1, p.page_2, p.weightedScore || 0]
                : [p.page_2, p.page_1, p.weightedScore || 0];

            const key = `${page1}-${page2}`;
            if (!pageMap.has(key)) pageMap.set(key, {page1, page2, scores: []});
            pageMap.get(key).scores.push(score);
            if (score < minScore) minScore = score;
            if (score > maxScore) maxScore = score;
        });

        const points = Array.from(pageMap.values()).map(({page1, page2, scores}) => ({
            page1, page2,
            score: scores.reduce((a, b) => a + b, 0) / scores.length,
            count: scores.length
        }));

        return {points, minScore, maxScore, doc1, doc2};
    }

    function renderMatrix() {
        if (!matrixContainer || !matrixData.docs.length) return;

        const {docs, matrix, maxScore} = matrixData;
        const size = docs.length * cellSize;

        d3.select(matrixContainer).selectAll('*').remove();

        const svg = d3.select(matrixContainer)
            .append('svg')
            .attr('width', size)
            .attr('height', size);

        const x = d3.scaleBand().range([0, size]).domain(d3.range(docs.length)).padding(0.02);

        const tooltip = d3.select('body').selectAll('.matrix-tooltip').data([0])
            .join('div')
            .attr('class', 'matrix-tooltip')
            .style('position', 'fixed')
            .style('background', 'var(--bulma-scheme-main)')
            .style('border', '1px solid var(--bulma-border)')
            .style('border-radius', '4px')
            .style('padding', '8px')
            .style('pointer-events', 'none')
            .style('opacity', 0)
            .style('font-size', '12px')
            .style('box-shadow', '0 2px 4px rgba(0,0,0,0.15)')
            .style('z-index', '9999')
            .style('color', 'var(--bulma-text)');

        const row = svg.selectAll('.row')
            .data(matrix)
            .join('g')
            .attr('class', 'row')
            .attr('transform', (d, i) => `translate(0,${x(i)})`);

        row.each(function (rowData) {
            d3.select(this).selectAll('.cell')
                .data(rowData.filter(d => !d.diagonal))
                .join('rect')
                .attr('class', 'cell')
                .attr('x', d => x(d.x))
                .attr('width', x.bandwidth())
                .attr('height', x.bandwidth())
                .attr('fill', d => {
                    if (d.z === 0) return 'var(--bulma-text)';
                    const color = d3.hsl(233, 0.951, 0.52);
                    color.opacity = maxScore > 0 ? 0.2 + 0.8 * (d.z / maxScore) : 0.2;
                    return color;
                })
                .attr('stroke', d => isSelected(d) ? 'var(--bulma-text)' : 'var(--bulma-scheme-main)')
                .attr('stroke-width', d => isSelected(d) ? 2 : 0.5)
                .style('cursor', 'pointer')
                .on('mouseover', function (event, d) {
                    if (!isSelected(d)) {
                        d3.select(this).attr('stroke', 'var(--bulma-text)').attr('stroke-width', 2);
                    }
                    tooltip.style('opacity', 1);
                })
                .on('mousemove', function (event, d) {
                    const content = d.z === 0
                        ? `<span style="color:${d.doc1.color}">●</span> ${d.doc1.title}<br/>↔<br/><span style="color:${d.doc2.color}">●</span> ${d.doc2.title}<br/><br/><em>${i18n('noPairs')}</em>`
                        : `<span style="color:${d.doc1.color}">●</span> ${d.doc1.title}<br/>↔<br/><span style="color:${d.doc2.color}">●</span> ${d.doc2.title}<br/><br/>${i18n('score')}: ${d.z.toFixed(2)}`;
                    tooltip
                        .html(content)
                        .style('left', (event.clientX + 15) + 'px')
                        .style('top', (event.clientY + 15) + 'px');
                })
                .on('mouseleave', function (event, d) {
                    if (!isSelected(d)) {
                        d3.select(this).attr('stroke', 'var(--bulma-scheme-main)').attr('stroke-width', 0.5);
                    }
                    tooltip.style('opacity', 0);
                })
                .on('click', (event, d) => {
                    selectedCell = {row: d.y, col: d.x, doc1: d.doc1, doc2: d.doc2};
                    updateSelection();
                });
        });

        svg.selectAll('.row').selectAll('.cell-diagonal')
            .data(d => d.filter(c => c.diagonal))
            .join('rect')
            .attr('class', 'cell-diagonal')
            .attr('x', d => x(d.x))
            .attr('width', x.bandwidth())
            .attr('height', x.bandwidth())
            .attr('fill', 'var(--contrasted)');
    }

    function isSelected(d) {
        return selectedCell && selectedCell.doc1.id === d.doc1.id && selectedCell.doc2.id === d.doc2.id;
    }

    function updateSelection() {
        if (!matrixContainer) return;
        d3.select(matrixContainer).selectAll('.cell')
            .attr('stroke', d => isSelected(d) ? 'var(--bulma-text)' : 'var(--bulma-scheme-main)')
            .attr('stroke-width', d => isSelected(d) ? 2 : 0.5);
    }

    function handleCellClick(page1, page2, doc1, doc2) {
        clickedPage = {page1, page2, doc1, doc2};
        modalElement?.classList.add('is-active');
    }

    function renderScatter() {
        if (!scatterContainer || !scatterData?.points.length) return;

        d3.select(scatterContainer).selectAll('*').remove();

        const {points, minScore, maxScore, doc1, doc2} = scatterData;

        const margin = {top: 65, right: 40, bottom: 20, left: 80};
        const heatmapHeight = 10;

        const maxPage1 = Math.max(...points.map(p => p.page1));
        const maxPage2 = Math.max(...points.map(p => p.page2));

        const plotWidth = maxPage1 * scatterCellSize;
        const plotHeight = maxPage2 * scatterCellSize;

        const pointMap = new Map(points.map(p => [`${p.page1}-${p.page2}`, p]));

        const svgWidth = plotWidth + margin.left + margin.right;
        const svgHeight = plotHeight + margin.top + margin.bottom;

        const svg = d3.select(scatterContainer)
            .append('svg')
            .attr('width', svgWidth)
            .attr('height', svgHeight);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const xScale = d3.scaleLinear().domain([0, maxPage1]).range([0, plotWidth]);
        const yScale = d3.scaleLinear().domain([0, maxPage2]).range([0, plotHeight]);

        const tooltip = d3.select('body').selectAll('.scatter-tooltip').data([0])
            .join('div')
            .attr('class', 'scatter-tooltip')
            .style('position', 'fixed')
            .style('background', 'var(--bulma-scheme-main)')
            .style('border', '1px solid var(--bulma-border)')
            .style('border-radius', '4px')
            .style('padding', '6px 10px')
            .style('pointer-events', 'none')
            .style('opacity', 0)
            .style('font-size', '11px')
            .style('box-shadow', '0 2px 4px rgba(0,0,0,0.15)')
            .style('z-index', '9999')
            .style('color', 'var(--bulma-text)');

        const xPageCounts = new Array(maxPage1).fill(0);
        const yPageCounts = new Array(maxPage2).fill(0);
        points.forEach(p => {
            xPageCounts[p.page1 - 1]++;
            yPageCounts[p.page2 - 1]++;
        });
        const xMaxCount = Math.max(...xPageCounts);
        const yMaxCount = Math.max(...yPageCounts);

        const xHeatmap = g.append('g').attr('transform', `translate(0,${-22 - heatmapHeight})`);
        xPageCounts.forEach((count, i) => {
            if (count === 0) return;
            xHeatmap.append('rect')
                .attr('x', i * scatterCellSize)
                .attr('width', scatterCellSize)
                .attr('height', heatmapHeight)
                .attr('fill', doc1.color)
                .attr('opacity', 0.15 + 0.85 * (count / xMaxCount))
                .style('cursor', 'default')
                .on('mouseover', () => tooltip.style('opacity', 1))
                .on('mousemove', (event) => {
                    tooltip
                        .html(`<strong>${count}</strong> image${count > 1 ? 's' : ''}<br/>${i18n('page')} ${i + 1}`)
                        .style('left', (event.clientX + 10) + 'px')
                        .style('top', (event.clientY - 30) + 'px');
                })
                .on('mouseleave', () => tooltip.style('opacity', 0));
        });

        const yHeatmap = g.append('g').attr('transform', `translate(-55,0)`);
        yPageCounts.forEach((count, i) => {
            if (count === 0) return;
            yHeatmap.append('rect')
                .attr('x', 0)
                .attr('y', i * scatterCellSize)
                .attr('width', heatmapHeight)
                .attr('height', scatterCellSize)
                .attr('fill', doc2.color)
                .attr('opacity', 0.15 + 0.85 * (count / yMaxCount))
                .style('cursor', 'default')
                .on('mouseover', () => tooltip.style('opacity', 1))
                .on('mousemove', (event) => {
                    tooltip
                        .html(`<strong>${count}</strong> image${count > 1 ? 's' : ''}<br/>${i18n('page')} ${i + 1}`)
                        .style('left', (event.clientX + 10) + 'px')
                        .style('top', (event.clientY - 30) + 'px');
                })
                .on('mouseleave', () => tooltip.style('opacity', 0));
        });

        g.append('g')
            .call(d3.axisTop(xScale).ticks(Math.min(maxPage1, 10)));

        g.append('g')
            .call(d3.axisLeft(yScale).ticks(Math.min(maxPage2, 10)));

        const truncate = (text, maxPx) => {
            const maxChars = Math.floor(maxPx / 6);
            return text.length > maxChars ? text.slice(0, maxChars - 1) + '…' : text;
        };

        const xLabel = g.append('g').attr('transform', `translate(${plotWidth / 2},${-50})`);
        xLabel.append('circle').attr('r', 4).attr('cx', -plotWidth / 2 + 4).attr('fill', doc1.color);
        xLabel.append('text')
            .attr('x', -plotWidth / 2 + 14)
            .attr('text-anchor', 'start')
            .attr('dominant-baseline', 'middle')
            .attr('font-size', '11px')
            .attr('fill', 'var(--bulma-text)')
            .text(truncate(`${doc1.title} (${i18n('page')})`, plotWidth - 20));

        const yLabel = g.append('g').attr('transform', `translate(-68,${plotHeight / 2}) rotate(-90)`);
        yLabel.append('circle').attr('r', 4).attr('cx', -plotHeight / 2 + 4).attr('fill', doc2.color);
        yLabel.append('text')
            .attr('x', -plotHeight / 2 + 14)
            .attr('text-anchor', 'start')
            .attr('dominant-baseline', 'middle')
            .attr('font-size', '11px')
            .attr('fill', 'var(--bulma-text)')
            .text(truncate(`${doc2.title} (${i18n('page')})`, plotHeight - 20));

        g.append('rect')
            .attr('class', 'hover-overlay')
            .attr('width', plotWidth)
            .attr('height', plotHeight)
            .attr('fill', 'transparent')
            .style('cursor', 'pointer')
            .on('mousemove', (event) => {
                const [mx, my] = d3.pointer(event, g.node());
                const p1 = Math.floor(mx / scatterCellSize) + 1;
                const p2 = Math.floor(my / scatterCellSize) + 1;
                if (p1 < 1 || p1 > maxPage1 || p2 < 1 || p2 > maxPage2) {
                    tooltip.style('opacity', 0);
                    return;
                }
                const point = pointMap.get(`${p1}-${p2}`);
                const tipTitle = `<span style="color:${doc1.color}">●</span> ${i18n('page')} ${p1}<br/><span style="color:${doc2.color}">●</span> ${i18n('page')} ${p2}`;
                const content = point
                    ? `${tipTitle}<br/>${i18n('score')}: ${point.score.toFixed(2)}`
                    : tipTitle;
                tooltip
                    .style('opacity', 1)
                    .html(content)
                    .style('left', (event.clientX + 10) + 'px')
                    .style('top', (event.clientY - 40) + 'px');
            })
            .on('mouseleave', () => tooltip.style('opacity', 0))
            .on('click', (event) => {
                const [mx, my] = d3.pointer(event, g.node());
                const p1 = Math.floor(mx / scatterCellSize) + 1;
                const p2 = Math.floor(my / scatterCellSize) + 1;
                if (p1 >= 1 && p1 <= maxPage1 && p2 >= 1 && p2 <= maxPage2) {
                    handleCellClick(p1, p2, doc1, doc2);
                }
            });

        g.selectAll('.cell')
            .data(points)
            .join('rect')
            .attr('class', 'cell')
            .attr('x', d => (d.page1 - 1) * scatterCellSize)
            .attr('y', d => (d.page2 - 1) * scatterCellSize)
            .attr('width', scatterCellSize)
            .attr('height', scatterCellSize)
            .attr('fill', d3.hsl(233, 0.951, 0.52))
            .attr('opacity', d => maxScore > minScore
                ? 0.2 + 0.8 * (d.score - minScore) / (maxScore - minScore)
                : 0.5)
            .attr('pointer-events', 'none');

        scatterContainer.style.width = svgWidth + 'px';
        scatterContainer.style.height = svgHeight + 'px';
    }

    function startDrag(e) {
        isDragging = true;
        e.preventDefault();
    }

    function onDrag(e) {
        if (!isDragging || !container) return;
        const rect = container.getBoundingClientRect();
        const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
        splitRatio = Math.max(0.2, Math.min(0.8, x / rect.width));
    }

    function stopDrag() {
        isDragging = false;
    }

    function getPageImageUrl(doc, pageNum) {
        const size = "full";
        return refToIIIF(`wit${doc.witnessId}_${doc.digitizationRef}_${String(pageNum).padStart(doc.zeros, '0')}`, "full", size);
    }

    onMount(() => {
        if (container) {
            containerWidth = container.offsetWidth;
            resizeObserver = new ResizeObserver(entries => {
                containerWidth = entries[0].contentRect.width;
            });
            resizeObserver.observe(container);
        }

        window.addEventListener('mousemove', onDrag);
        window.addEventListener('mouseup', stopDrag);
        window.addEventListener('touchmove', onDrag);
        window.addEventListener('touchend', stopDrag);
    });

    onDestroy(() => {
        resizeObserver?.disconnect();
        window.removeEventListener('mousemove', onDrag);
        window.removeEventListener('mouseup', stopDrag);
        window.removeEventListener('touchmove', onDrag);
        window.removeEventListener('touchend', stopDrag);
    });

    $: if (matrixContainer && matrixData.docs.length) renderMatrix();
    $: if (scatterContainer && scatterData) renderScatter();
</script>

<div class="split-container" bind:this={container}>
    {#if !documents.length}
        <div class="notification is-info" style="width: 100%">{i18n('noDocuments')}</div>
    {:else}
        <div class="split-panel" style="width: {leftWidth}px;">
            <div class="box panel-box">
                <div class="is-flex is-justify-content-space-between is-align-items-center mb-3">
                    <h4 class="title is-6 mb-0">{i18n('title')}</h4>
                    <div class="field mb-0">
                        <div class="control">
                            <div class="select is-small">
                                <select bind:value={sortOrder}>
                                    <option value="name">{i18n('byName')}</option>
                                    <option value="score">{i18n('byScore')}</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="scroll-area">
                    <div class="matrix-grid" style="--cell-size: {cellSize}px;">
                        <div class="matrix-corner"></div>
                        <div class="col-headers">
                            {#each matrixData.docs as doc (doc.id)}
                                <div class="header-cell">
                                    <span class="color-dot" style="background-color: {doc.color}" title={doc.title}></span>
                                </div>
                            {/each}
                        </div>
                        <div class="row-headers">
                            {#each matrixData.docs as doc (doc.id)}
                                <div class="header-cell">
                                    <span class="color-dot" style="background-color: {doc.color}" title={doc.title}></span>
                                </div>
                            {/each}
                        </div>
                        <div class="matrix-canvas" bind:this={matrixContainer}></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="split-divider" on:mousedown={startDrag} on:touchstart={startDrag} role="separator" tabindex="0"></div>

        <div class="split-panel" style="width: {rightWidth}px;">
            <div class="box panel-box">
                <h4 class="title is-6 mb-3">{i18n('pageByPage')}</h4>
                <div class="scroll-area">
                    {#if selectedCell}
                        <div class="scatter-container" bind:this={scatterContainer}></div>
                    {:else}
                        <p class="has-text-grey is-size-7">{i18n('selectCell')}</p>
                    {/if}
                </div>
            </div>
        </div>
    {/if}
</div>

<div id="matrix-page-modal" class="modal" bind:this={modalElement} use:closeModal>
    <div class="modal-background"></div>
    <div class="modal-content" style="width: auto; max-width: 70vw;">
        <div class="box p-5">
            {#if clickedPage}
                <table class="table is-fullwidth p-3 has-text-centered">
                    <thead>
                        <tr>
                            {#each [1, 2] as nb}
                                <th class="doc-title">
                                    <span style="color:{clickedPage[`doc${nb}`].color}">●</span>
                                    <strong>{clickedPage[`doc${nb}`].title}</strong>
                                </th>
                            {/each}
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            {#each [1, 2] as nb}
                                <td>
                                    <p class="is-size-7 has-text-grey mb-3">{i18n('page')} {clickedPage[`page${nb}`]}</p>
                                    <figure class="image">
                                        <img src={getPageImageUrl(clickedPage[`doc${nb}`], clickedPage[`page${nb}`])}
                                             alt="Page {clickedPage[`page${nb}`]}"/>
                                    </figure>
                                </td>
                            {/each}
                        </tr>
                    </tbody>
                </table>
            {/if}
        </div>
    </div>
    <button class="modal-close is-large" aria-label="close"></button>
</div>

<style>
    .split-container {
        display: flex;
        gap: 0;
        user-select: none;
    }

    .split-panel {
        flex-shrink: 0;
        min-width: 0;
        height: 100%;
    }

    .split-divider {
        width: 8px;
        cursor: col-resize;
        background: transparent;
        position: relative;
        flex-shrink: 0;
    }

    .split-divider::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 4px;
        height: 40px;
        background: var(--bulma-border);
        border-radius: 2px;
    }

    .split-divider:hover::after {
        background: var(--bulma-link);
    }

    .panel-box {
        height: 100%;
        display: flex;
        flex-direction: column;
    }

    .scroll-area {
        flex: 1;
        overflow: auto;
        max-height: calc(100vh - 250px);
    }

    .matrix-grid {
        display: grid;
        grid-template-columns: var(--cell-size) auto;
        grid-template-rows: var(--cell-size) auto;
        width: fit-content;
    }

    .matrix-corner {
        grid-row: 1;
        grid-column: 1;
    }

    .col-headers {
        grid-row: 1;
        grid-column: 2;
        display: flex;
    }

    .row-headers {
        grid-row: 2;
        grid-column: 1;
        display: flex;
        flex-direction: column;
    }

    .header-cell {
        width: var(--cell-size);
        height: var(--cell-size);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .color-dot {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }

    .matrix-canvas {
        grid-row: 2;
        grid-column: 2;
    }

    .scatter-container {
        display: block;
    }

    .doc-title {
        width: 50%;
        text-align: center !important;
        vertical-align: middle;
    }
</style>

<script>
    import * as d3 from 'd3';
    import {appLang, model2title} from '../constants.js';
    import {onMount, onDestroy} from 'svelte';
    import {closeModal, refToIIIF} from '../utils.js';

    export let documentSetStore;

    const {
        documentNodes, pairIndex, activeDocPairStats, activeDocStats,
        imageCountMap, visiblePairIds, matrixMode, normalizeByImages
    } = documentSetStore;

    const t = {
        title: {en: 'Document Matrix', fr: 'Matrice de documents'},
        order: {en: 'Order', fr: 'Ordre'},
        byName: {en: 'By title', fr: 'Par titre'},
        byScore: {en: 'By score', fr: 'Par score'},
        noDocuments: {en: 'No documents available', fr: 'Aucun document disponible'},
        pageByPage: {en: 'Page-by-page similarity', fr: 'Similarité page par page'},
        page: {en: 'page', fr: 'page'},
        score: {en: 'Score', fr: 'Score'},
        noPairs: {en: 'No pairs', fr: 'Aucune paire'},
        selectCell: {en: 'Click a cell to view page-by-page similarity', fr: 'Cliquez sur une cellule pour voir la similarité page par page'},
        byPage: {en: 'By page', fr: 'Par page'},
        byImage: {en: 'By image', fr: 'Par image'},
        image: {en: 'image', fr: 'image'},
        normalize: {en: 'Normalize', fr: 'Normaliser'},
        normalization: {en: 'Normalization by document image counts', fr: "Normalisation par le nombre d'images des documents"},
        allPairs: {en: 'All pairs in the document set', fr: 'Toutes les paires du corpus'},
        filteredPairs: {en: 'Filtered pairs', fr: 'Paires après filtrage'},
        filtering: {en: 'Source of image pairs for the visualizations', fr: "Source des paires d’images pour les visualisations"},
    };
    const i18n = (key) => t[key]?.[appLang] || t[key]?.en || key;

    let container, matrixContainer, scatterContainer, modalElement;
    let selectedCell = null;
    let sortOrder = 'name';
    let splitRatio = 0.5;
    let isDragging = false;
    let containerWidth = 0;
    let resizeObserver;
    let navState = null; // {idx1, idx2}
    let scatterMode = 'page';

    const MIN_WIDTH = 300;
    const cellSize = 30;
    const scatterCellSize = 5;

    $: documents = Array.from($documentNodes?.values() || []);
    $: matrixData = buildMatrix(documents, $activeDocPairStats.scoreCount, $activeDocStats.scoreCount, sortOrder, $normalizeByImages, $imageCountMap);
    $: scatterData = selectedCell ? buildScatter(selectedCell, scatterMode, $matrixMode === 'filtered', $visiblePairIds) : null;
    $: leftWidth = Math.max(MIN_WIDTH, containerWidth * splitRatio - 4);
    $: rightWidth = Math.max(MIN_WIDTH, containerWidth * (1 - splitRatio) - 4);
    $: navLimits = scatterData ? getNavLimits(scatterData) : {max1: 0, max2: 0, pages1: [], pages2: []};
    $: modalData = navState && scatterData && navLimits ? buildModalData(navState, scatterData, navLimits) : null;

    function getNavLimits(data) {
        if (data.mode === 'image') {
            return {max1: data.images1.length, max2: data.images2.length};
        }
        const maxPage1 = Math.max(...data.points.map(p => p.page1));
        const maxPage2 = Math.max(...data.points.map(p => p.page2));
        return {max1: maxPage1, max2: maxPage2};
    }

    function getPageImageUrl(doc, pageNum) {
        const size = "full";
        return refToIIIF(`wit${doc.witnessId}_${doc.digitizationRef}_${String(pageNum).padStart(doc.zeros, '0')}`, "full", size);
    }

    function getRegionImageUrl(img) {
        return refToIIIF(img.ref, img.xywh?.join(','), "full");
    }

    function buildModalData(nav, data, limits) {
        if (!nav || !data || !limits) return null;
        const {doc1, doc2} = data;

        if (data.mode === 'image') {
            const img1 = data.images1?.[nav.idx1];
            const img2 = data.images2?.[nav.idx2];
            if (!img1 || !img2) return null;

            const pairKey = `${nav.idx1}-${nav.idx2}`;
            const pair = data.pairScores.get(pairKey);

            return {
                items: [
                    {doc: doc1, label: `Page ${img1.canvas} Image #${nav.idx1 + 1}`, imgUrl: getRegionImageUrl(img1)},
                    {doc: doc2, label: `Page ${img2.canvas} Image #${nav.idx2 + 1}`, imgUrl: getRegionImageUrl(img2)}
                ],
                score: pair?.score
            };
        }

        const page1 = nav.idx1 + 1;
        const page2 = nav.idx2 + 1;
        const point = data.points.find(p => p.page1 === page1 && p.page2 === page2);

        return {
            items: [
                {doc: doc1, label: `Page ${page1}`, imgUrl: getPageImageUrl(doc1, page1)},
                {doc: doc2, label: `Page ${page2}`, imgUrl: getPageImageUrl(doc2, page2)}
            ],
            score: point?.score
        };
    }

    function navigate(axis, delta) {
        if (!navState || !scatterData) return;

        if (axis === 'horizontal') {
            navState.idx1 = (navState.idx1 + delta + navLimits.max1) % navLimits.max1;
        } else {
            navState.idx2 = (navState.idx2 + delta + navLimits.max2) % navLimits.max2;
        }
        navState = navState; // trigger reactivity
    }

    function handleKeydown(e) {
        if (!navState || !modalElement?.classList.contains('is-active')) return;

        const keyMap = {
            ArrowUp: ['vertical', -1],
            ArrowDown: ['vertical', 1],
            ArrowLeft: ['horizontal', -1],
            ArrowRight: ['horizontal', 1]
        };

        const action = keyMap[e.key];
        if (action) {
            e.preventDefault();
            navigate(action[0], action[1]);
        }
    }

    function buildMatrix(docs, scoreCount, docStats, order, normalize, imageCount) {
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
                    let score = scoreCount?.get(key)?.score || 0;

                    if (normalize && score > 0) {
                        const n1 = imageCount.get(sorted[i].id) || 1;
                        const n2 = imageCount.get(sorted[j].id) || 1;
                        score /= Math.sqrt(n1 * n2);
                    }

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

    function buildScatter(cell, mode, filterPairs, visibleIds) {
        const {doc1, doc2} = cell;
        const pairKey = doc1.id < doc2.id ? `${doc1.id}-${doc2.id}` : `${doc2.id}-${doc1.id}`;
        let pairs = $pairIndex.byDocPair.get(pairKey) || [];

        if (filterPairs && visibleIds.size > 0) {
            pairs = pairs.filter(p => visibleIds.has(`${p.id_1}-${p.id_2}`));
        }

        if (!pairs.length) return null;

        return mode === 'image'
            ? buildImageScatter(doc1, doc2, pairs)
            : buildPageScatter(doc1, doc2, pairs);
    }

    function buildPageScatter(doc1, doc2, pairs) {
        const pageMap = new Map();
        let minScore = Infinity, maxScore = -Infinity;

        for (const p of pairs) {
            const [page1, page2, score] = p.regions_id_1 === doc1.id
                ? [p.page_1, p.page_2, p.weightedScore || 0]
                : [p.page_2, p.page_1, p.weightedScore || 0];

            const key = `${page1}-${page2}`;
            if (!pageMap.has(key)) pageMap.set(key, {page1, page2, scores: []});
            pageMap.get(key).scores.push(score);
            if (score < minScore) minScore = score;
            if (score > maxScore) maxScore = score;
        }

        const points = Array.from(pageMap.values()).map(({page1, page2, scores}) => ({
            page1, page2,
            score: scores.reduce((a, b) => a + b, 0) / scores.length,
            count: scores.length
        }));

        return {mode: 'page', points, minScore, maxScore, doc1, doc2};
    }

    function buildImageScatter(doc1, doc2, pairs) {
        const images1 = doc1.images || [];
        const images2 = doc2.images || [];

        if (!images1.length || !images2.length) return null;

        const imgIndex1 = new Map(images1.map((img, i) => [img.id, i]));
        const imgIndex2 = new Map(images2.map((img, i) => [img.id, i]));

        const pairScores = new Map();
        let minScore = Infinity, maxScore = -Infinity;

        pairs.forEach(p => {
            const [imgId1, imgId2, score] = p.regions_id_1 === doc1.id
                ? [p.id_1, p.id_2, p.weightedScore || 0]
                : [p.id_2, p.id_1, p.weightedScore || 0];

            const idx1 = imgIndex1.get(imgId1);
            const idx2 = imgIndex2.get(imgId2);

            if (idx1 !== undefined && idx2 !== undefined) {
                const key = `${idx1}-${idx2}`;
                pairScores.set(key, {idx1, idx2, imgId1, imgId2, score});
                if (score < minScore) minScore = score;
                if (score > maxScore) maxScore = score;
            }
        });

        return {
            mode: 'image',
            images1,
            images2,
            pairScores,
            minScore,
            maxScore,
            doc1,
            doc2
        };
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
                    const docs = `<span style="color:${d.doc1.color}">●</span> ${d.doc1.title}<br/>↔<br/><span style="color:${d.doc2.color}">●</span> ${d.doc2.title}`
                    const content = d.z === 0
                        ? `${docs}<br/><br/><em>${i18n('noPairs')}</em>`
                        : `${docs}<br/><br/>${i18n('score')}: ${d.z.toFixed(2)}`;

                    // if (d.z === 0) {
                    //     // marker
                    //     console.log(d.doc1.witnessId, "↔", d.doc2.witnessId);
                    // }

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

    function renderScatter() {
        if (!scatterContainer || !scatterData) return;
        d3.select(scatterContainer).selectAll('*').remove();

        if (scatterData.mode === 'image') {
            renderImageScatter();
        } else {
            renderPageScatter();
        }
    }

    function renderPageScatter() {
        const {points, minScore, maxScore, doc1, doc2} = scatterData;
        if (!points.length) return;

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

        g.append('g').call(d3.axisTop(xScale).ticks(Math.min(maxPage1, 10)));
        g.append('g').call(d3.axisLeft(yScale).ticks(Math.min(maxPage2, 10)));

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

                if (p1 < 1 || p1 > maxPage1 || p2 < 1 || p2 > maxPage2) return;

                navState = {idx1: p1 - 1, idx2: p2 - 1};
                modalElement?.classList.add('is-active');
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

    function renderImageScatter() {
        const {images1, images2, pairScores, minScore, maxScore, doc1, doc2} = scatterData;
        if (!images1.length || !images2.length) return;

        const margin = {top: 65, right: 40, bottom: 20, left: 80};
        const heatmapHeight = 10;

        const plotWidth = images1.length * scatterCellSize;
        const plotHeight = images2.length * scatterCellSize;

        const svgWidth = plotWidth + margin.left + margin.right;
        const svgHeight = plotHeight + margin.top + margin.bottom;

        const svg = d3.select(scatterContainer)
            .append('svg')
            .attr('width', svgWidth)
            .attr('height', svgHeight);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const xScale = d3.scaleLinear().domain([0, images1.length]).range([0, plotWidth]);
        const yScale = d3.scaleLinear().domain([0, images2.length]).range([0, plotHeight]);

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

        const pageBoundaries1 = getPageBoundaries(images1);
        const pageBoundaries2 = getPageBoundaries(images2);

        const xHeatmap = g.append('g').attr('transform', `translate(0,${-22 - heatmapHeight})`);
        pageBoundaries1.forEach(({start, end, page, count}) => {
            xHeatmap.append('rect')
                .attr('x', start * scatterCellSize)
                .attr('width', (end - start) * scatterCellSize)
                .attr('height', heatmapHeight)
                .attr('fill', doc1.color)
                .attr('opacity', 0.5)
                .style('cursor', 'default')
                .on('mouseover', () => tooltip.style('opacity', 1))
                .on('mousemove', (event) => {
                    tooltip
                        .html(`${i18n('page')} ${page}<br/><strong>${count}</strong> image${count > 1 ? 's' : ''}`)
                        .style('left', (event.clientX + 10) + 'px')
                        .style('top', (event.clientY - 30) + 'px');
                })
                .on('mouseleave', () => tooltip.style('opacity', 0));
        });

        const yHeatmap = g.append('g').attr('transform', `translate(-55,0)`);
        pageBoundaries2.forEach(({start, end, page, count}) => {
            yHeatmap.append('rect')
                .attr('x', 0)
                .attr('y', start * scatterCellSize)
                .attr('width', heatmapHeight)
                .attr('height', (end - start) * scatterCellSize)
                .attr('fill', doc2.color)
                .attr('opacity', 0.5)
                .style('cursor', 'default')
                .on('mouseover', () => tooltip.style('opacity', 1))
                .on('mousemove', (event) => {
                    tooltip
                        .html(`${i18n('page')} ${page}<br/><strong>${count}</strong> image${count > 1 ? 's' : ''}`)
                        .style('left', (event.clientX + 10) + 'px')
                        .style('top', (event.clientY - 30) + 'px');
                })
                .on('mouseleave', () => tooltip.style('opacity', 0));
        });

        g.append('g').call(d3.axisTop(xScale).ticks(Math.min(images1.length, 10)));
        g.append('g').call(d3.axisLeft(yScale).ticks(Math.min(images2.length, 10)));

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
            .text(truncate(`${doc1.title} (${i18n('image')})`, plotWidth - 20));

        const yLabel = g.append('g').attr('transform', `translate(-68,${plotHeight / 2}) rotate(-90)`);
        yLabel.append('circle').attr('r', 4).attr('cx', -plotHeight / 2 + 4).attr('fill', doc2.color);
        yLabel.append('text')
            .attr('x', -plotHeight / 2 + 14)
            .attr('text-anchor', 'start')
            .attr('dominant-baseline', 'middle')
            .attr('font-size', '11px')
            .attr('fill', 'var(--bulma-text)')
            .text(truncate(`${doc2.title} (${i18n('image')})`, plotHeight - 20));

        g.append('rect')
            .attr('class', 'hover-overlay')
            .attr('width', plotWidth)
            .attr('height', plotHeight)
            .attr('fill', 'transparent')
            .style('cursor', 'pointer')
            .on('mousemove', (event) => {
                const [mx, my] = d3.pointer(event, g.node());
                const idx1 = Math.floor(mx / scatterCellSize);
                const idx2 = Math.floor(my / scatterCellSize);
                if (idx1 < 0 || idx1 >= images1.length || idx2 < 0 || idx2 >= images2.length) {
                    tooltip.style('opacity', 0);
                    return;
                }
                const img1 = images1[idx1];
                const img2 = images2[idx2];
                const pair = pairScores.get(`${idx1}-${idx2}`);
                const tipTitle = `<span style="color:${doc1.color}">●</span> ${i18n('page')} ${img1.canvas}, ${i18n('image')} ${idx1 + 1}<br/><span style="color:${doc2.color}">●</span> ${i18n('page')} ${img2.canvas}, ${i18n('image')} ${idx2 + 1}`;
                const content = pair
                    ? `${tipTitle}<br/>${i18n('score')}: ${pair.score.toFixed(2)}`
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
                const idx1 = Math.floor(mx / scatterCellSize);
                const idx2 = Math.floor(my / scatterCellSize);
                if (idx1 >= 0 && idx1 < images1.length && idx2 >= 0 && idx2 < images2.length) {
                    navState = {idx1, idx2};
                    modalElement?.classList.add('is-active');
                }
            });


        const cellData = Array.from(pairScores.values());
        g.selectAll('.cell')
            .data(cellData)
            .join('rect')
            .attr('class', 'cell')
            .attr('x', d => d.idx1 * scatterCellSize)
            .attr('y', d => d.idx2 * scatterCellSize)
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

    function getPageBoundaries(images) {
        const boundaries = [];
        let currentPage = null;
        let start = 0;

        images.forEach((img, i) => {
            if (img.canvas !== currentPage) {
                if (currentPage !== null) {
                    boundaries.push({start, end: i, page: currentPage, count: i - start});
                }
                currentPage = img.canvas;
                start = i;
            }
        });
        if (currentPage !== null) {
            boundaries.push({start, end: images.length, page: currentPage, count: images.length - start});
        }
        return boundaries;
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
        window.addEventListener('keydown', handleKeydown);
    });

    onDestroy(() => {
        resizeObserver?.disconnect();
        window.removeEventListener('mousemove', onDrag);
        window.removeEventListener('mouseup', stopDrag);
        window.removeEventListener('touchmove', onDrag);
        window.removeEventListener('touchend', stopDrag);
        window.removeEventListener('keydown', handleKeydown);
    });

    $: if (matrixContainer && matrixData.docs.length) renderMatrix();
    $: if (scatterContainer && scatterData) renderScatter();
</script>

<div class="field mb-4">
    <label class="label is-small" for="matrix-mode">
        {i18n('filtering')}
    </label>

    <div class="control">
        <div class="select is-small is-fullwidth">
            <select id="matrix-mode" bind:value={$matrixMode}>
                <option value="all">{i18n('allPairs')}</option>
                <option value="filtered">{i18n('filteredPairs')}</option>
            </select>
        </div>
    </div>
</div>

<div class="split-container" bind:this={container}>
    {#if !documents.length}
        <div class="notification is-info" style="width: 100%">{i18n('noDocuments')}</div>
    {:else}
        <div class="split-panel" style="width: {leftWidth}px;">
            <div class="box panel-box">
                <div class="is-flex is-justify-content-space-between is-align-items-center mb-3" style="flex-wrap: wrap; gap: 0.5rem;">
                    <h4 class="title is-6 mb-0">{i18n('title')}</h4>
                    <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
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

                <div class="scroll-area">
                    <div class="matrix-grid" style="--cell-size: {cellSize}px;">
                        <div class="matrix-corner"></div>
                        {#each ["col", "row"] as side}
                            <div class="{side}-headers">
                                {#each matrixData.docs as doc (doc.id)}
                                    <div class="header-cell">
                                        <span class="color-dot" style="background-color: {doc.color}" title="{doc.title} {model2title.Witness} #{doc.witnessId}"></span>
                                    </div>
                                {/each}
                            </div>
                        {/each}
                        <div class="matrix-canvas" bind:this={matrixContainer}></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="split-divider" on:mousedown={startDrag} on:touchstart={startDrag} role="separator" tabindex="0"></div>

        <div class="split-panel" style="width: {rightWidth}px;">
            <div class="box panel-box">
                <div class="is-flex is-justify-content-space-between is-align-items-center mb-3">
                    <h4 class="title is-6 mb-0">{i18n('pageByPage')}</h4>
                    {#if selectedCell}
                        <div class="field mb-0">
                            <div class="control">
                                <div class="select is-small">
                                    <select bind:value={scatterMode}>
                                        <option value="page">{i18n('byPage')}</option>
                                        <option value="image">{i18n('byImage')}</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    {/if}
                </div>
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
            {#if modalData}
                <table class="table is-fullwidth p-3 has-text-centered">
                    <thead>
                        <tr>
                            {#each modalData.items as item, _}
                                <th class="doc-title">
                                    <span style="color:{item.doc.color}">●</span>
                                    <strong>{item.doc.title}</strong>
                                </th>
                            {/each}
                        </tr>
                    </thead>
                    <tbody>
                        {#if modalData.score !== undefined}
                            <tr>
                                <td colspan="2" class="has-text-centered">
                                    <span class="tag is-small">{i18n('score')} <b>{modalData.score.toFixed(2)}</b></span>
                                </td>
                            </tr>
                        {/if}
                        <tr>
                            {#each modalData.items as item, i}
                                <td class="modal-cell">
                                    <p class="is-size-7 has-text-grey mb-2">{item.label}</p>
                                    <div class="image-nav-container">
                                        <button class="nav-btn {i !== 0 ? 'nav-up' : 'nav-left'}"
                                                on:click={() => navigate(i !== 0 ? 'vertical' : 'horizontal', -1)}>
                                            {#if i !== 0}
                                                <span class="icon is-small p-0">
                                                    <i class="fas fa-chevron-up"></i>
                                                </span>
                                            {:else}
                                                <span class="icon is-small p-0">
                                                    <i class="fas fa-chevron-left"></i>
                                                </span>
                                            {/if}
                                        </button>
                                        <figure class="image">
                                            <img src={item.imgUrl} alt="{scatterData?.mode === 'image' ? 'Image' : 'Page'} {item.label}" class="img-preview"/>
                                        </figure>
                                        <button class="nav-btn {i !== 0 ? 'nav-down' : 'nav-right'}"
                                                on:click={() => navigate(i !== 0 ? 'vertical' : 'horizontal', 1)}>
                                            {#if i !== 0}
                                                <span class="icon is-small">
                                                    <i class="fas fa-chevron-down"></i>
                                                </span>
                                            {:else}
                                                <span class="icon is-small">
                                                    <i class="fas fa-chevron-right"></i>
                                                </span>
                                            {/if}
                                        </button>
                                    </div>
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

    .modal-cell {
        width: 50%;
        vertical-align: middle;
    }

    .image-nav-container {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 1em;
        margin-bottom: 1em;
    }

    .nav-btn {
        position: absolute;
        color: var(--bulma-link);
        cursor: pointer;
        z-index: 1;
    }

    .nav-up { top: 0; }
    .nav-down { bottom: 0; }
    .nav-left { left: 0; top: 50%; transform: translateY(-50%); }
    .nav-right { right: 0; top: 50%; transform: translateY(-50%); }

    .img-preview {
        border-radius: 5px;
        max-height: 600px;
        max-width: 90%;
        margin: 2em auto 2em auto;
    }
</style>

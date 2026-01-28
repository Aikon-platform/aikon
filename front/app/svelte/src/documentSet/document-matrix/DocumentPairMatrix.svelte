<script>
    import * as d3 from 'd3';
    import {createEventDispatcher} from 'svelte';
    import {appLang} from '../../constants.js';

    export let doc1 = null;
    export let doc2 = null;
    export let pairs = [];
    export let mode = 'page'; // 'page' | 'image'
    export let cellSize = 5;

    const dispatch = createEventDispatcher();

    const t = {
        page: {en: 'page', fr: 'page'},
        image: {en: 'image', fr: 'image'},
        score: {en: 'Score', fr: 'Score'},
    };
    const i18n = (key) => t[key]?.[appLang] || t[key]?.en || key;

    let container;

    $: scatterData = doc1 && doc2 && pairs.length ? buildScatter(doc1, doc2, pairs, mode) : null;
    $: if (container && scatterData) render();

    function buildScatter(d1, d2, pairList, m) {
        return m === 'image' ? buildImageScatter(d1, d2, pairList) : buildPageScatter(d1, d2, pairList);
    }

    function buildPageScatter(d1, d2, pairList) {
        const pageMap = new Map();
        let minScore = Infinity, maxScore = -Infinity;

        for (const p of pairList) {
            const [page1, page2, score] = p.regions_id_1 === d1.id
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

        return {mode: 'page', points, minScore, maxScore, doc1: d1, doc2: d2};
    }

    function buildImageScatter(d1, d2, pairList) {
        const images1 = d1.images || [];
        const images2 = d2.images || [];
        if (!images1.length || !images2.length) return null;

        const imgIndex1 = new Map(images1.map((img, i) => [img.id, i]));
        const imgIndex2 = new Map(images2.map((img, i) => [img.id, i]));

        const pairScores = new Map();
        let minScore = Infinity, maxScore = -Infinity;

        pairList.forEach(p => {
            const [imgId1, imgId2, score] = p.regions_id_1 === d1.id
                ? [p.id_1, p.id_2, p.weightedScore || 0]
                : [p.id_2, p.id_1, p.weightedScore || 0];

            const idx1 = imgIndex1.get(imgId1);
            const idx2 = imgIndex2.get(imgId2);

            if (idx1 !== undefined && idx2 !== undefined) {
                pairScores.set(`${idx1}-${idx2}`, {idx1, idx2, imgId1, imgId2, score});
                if (score < minScore) minScore = score;
                if (score > maxScore) maxScore = score;
            }
        });

        return {mode: 'image', images1, images2, pairScores, minScore, maxScore, doc1: d1, doc2: d2};
    }

    function getPageBoundaries(images) {
        const boundaries = [];
        let currentPage = null, start = 0;

        images.forEach((img, i) => {
            if (img.canvas !== currentPage) {
                if (currentPage !== null) boundaries.push({start, end: i, page: currentPage, count: i - start});
                currentPage = img.canvas;
                start = i;
            }
        });
        if (currentPage !== null) boundaries.push({start, end: images.length, page: currentPage, count: images.length - start});
        return boundaries;
    }

    function render() {
        if (!container || !scatterData) return;
        d3.select(container).selectAll('*').remove();
        scatterData.mode === 'image' ? renderImageScatter() : renderPageScatter();
    }

    function renderPageScatter() {
        const {points, minScore, maxScore, doc1: d1, doc2: d2} = scatterData;
        if (!points.length) return;

        const margin = {top: 65, right: 40, bottom: 20, left: 80};
        const heatmapHeight = 10;
        const maxPage1 = Math.max(...points.map(p => p.page1));
        const maxPage2 = Math.max(...points.map(p => p.page2));
        const plotWidth = maxPage1 * cellSize;
        const plotHeight = maxPage2 * cellSize;
        const pointMap = new Map(points.map(p => [`${p.page1}-${p.page2}`, p]));

        const svg = d3.select(container).append('svg')
            .attr('width', plotWidth + margin.left + margin.right)
            .attr('height', plotHeight + margin.top + margin.bottom);

        const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);
        const xScale = d3.scaleLinear().domain([0, maxPage1]).range([0, plotWidth]);
        const yScale = d3.scaleLinear().domain([0, maxPage2]).range([0, plotHeight]);

        const tooltip = createTooltip();

        const xPageCounts = new Array(maxPage1).fill(0);
        const yPageCounts = new Array(maxPage2).fill(0);
        points.forEach(p => { xPageCounts[p.page1 - 1]++; yPageCounts[p.page2 - 1]++; });
        const xMaxCount = Math.max(...xPageCounts);
        const yMaxCount = Math.max(...yPageCounts);

        renderHeatmapBar(g, xPageCounts, xMaxCount, d1.color, 'x', heatmapHeight, tooltip);
        renderHeatmapBar(g, yPageCounts, yMaxCount, d2.color, 'y', heatmapHeight, tooltip);

        g.append('g').call(d3.axisTop(xScale).ticks(Math.min(maxPage1, 10)));
        g.append('g').call(d3.axisLeft(yScale).ticks(Math.min(maxPage2, 10)));

        renderAxisLabel(g, d1, plotWidth, plotHeight, 'x', i18n('page'));
        renderAxisLabel(g, d2, plotWidth, plotHeight, 'y', i18n('page'));

        g.append('rect')
            .attr('width', plotWidth).attr('height', plotHeight)
            .attr('fill', 'transparent').style('cursor', 'pointer')
            .on('mousemove', (event) => {
                const [mx, my] = d3.pointer(event, g.node());
                const p1 = Math.floor(mx / cellSize) + 1;
                const p2 = Math.floor(my / cellSize) + 1;
                if (p1 < 1 || p1 > maxPage1 || p2 < 1 || p2 > maxPage2) { tooltip.style('opacity', 0); return; }
                const point = pointMap.get(`${p1}-${p2}`);
                const tip = `<span style="color:${d1.color}">●</span> ${i18n('page')} ${p1}<br/><span style="color:${d2.color}">●</span> ${i18n('page')} ${p2}`;
                tooltip.style('opacity', 1).html(point ? `${tip}<br/>${i18n('score')}: ${point.score.toFixed(2)}` : tip)
                    .style('left', (event.clientX + 10) + 'px').style('top', (event.clientY - 40) + 'px');
            })
            .on('mouseleave', () => tooltip.style('opacity', 0))
            .on('click', (event) => {
                const [mx, my] = d3.pointer(event, g.node());
                const p1 = Math.floor(mx / cellSize) + 1, p2 = Math.floor(my / cellSize) + 1;
                if (p1 >= 1 && p1 <= maxPage1 && p2 >= 1 && p2 <= maxPage2) {
                    dispatch('cellclick', {idx1: p1 - 1, idx2: p2 - 1, mode: 'page', data: scatterData});
                }
            });

        g.selectAll('.cell').data(points).join('rect')
            .attr('class', 'cell')
            .attr('x', d => (d.page1 - 1) * cellSize).attr('y', d => (d.page2 - 1) * cellSize)
            .attr('width', cellSize).attr('height', cellSize)
            .attr('fill', d3.hsl(233, 0.951, 0.52))
            .attr('opacity', d => maxScore > minScore ? 0.2 + 0.8 * (d.score - minScore) / (maxScore - minScore) : 0.5)
            .attr('pointer-events', 'none');

        container.style.width = (plotWidth + margin.left + margin.right) + 'px';
        container.style.height = (plotHeight + margin.top + margin.bottom) + 'px';
    }

    function renderImageScatter() {
        const {images1, images2, pairScores, minScore, maxScore, doc1: d1, doc2: d2} = scatterData;
        if (!images1.length || !images2.length) return;

        const margin = {top: 65, right: 40, bottom: 20, left: 80};
        const heatmapHeight = 10;
        const plotWidth = images1.length * cellSize;
        const plotHeight = images2.length * cellSize;

        const svg = d3.select(container).append('svg')
            .attr('width', plotWidth + margin.left + margin.right)
            .attr('height', plotHeight + margin.top + margin.bottom);

        const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);
        const xScale = d3.scaleLinear().domain([0, images1.length]).range([0, plotWidth]);
        const yScale = d3.scaleLinear().domain([0, images2.length]).range([0, plotHeight]);

        const tooltip = createTooltip();

        const pageBoundaries1 = getPageBoundaries(images1);
        const pageBoundaries2 = getPageBoundaries(images2);

        renderPageBoundaries(g, pageBoundaries1, d1.color, 'x', heatmapHeight, tooltip);
        renderPageBoundaries(g, pageBoundaries2, d2.color, 'y', heatmapHeight, tooltip);

        g.append('g').call(d3.axisTop(xScale).ticks(Math.min(images1.length, 10)));
        g.append('g').call(d3.axisLeft(yScale).ticks(Math.min(images2.length, 10)));

        renderAxisLabel(g, d1, plotWidth, plotHeight, 'x', i18n('image'));
        renderAxisLabel(g, d2, plotWidth, plotHeight, 'y', i18n('image'));

        g.append('rect')
            .attr('width', plotWidth).attr('height', plotHeight)
            .attr('fill', 'transparent').style('cursor', 'pointer')
            .on('mousemove', (event) => {
                const [mx, my] = d3.pointer(event, g.node());
                const idx1 = Math.floor(mx / cellSize), idx2 = Math.floor(my / cellSize);
                if (idx1 < 0 || idx1 >= images1.length || idx2 < 0 || idx2 >= images2.length) { tooltip.style('opacity', 0); return; }
                const img1 = images1[idx1], img2 = images2[idx2];
                const pair = pairScores.get(`${idx1}-${idx2}`);
                const tip = `<span style="color:${d1.color}">●</span> ${i18n('page')} ${img1.canvas}, ${i18n('image')} ${idx1 + 1}<br/><span style="color:${d2.color}">●</span> ${i18n('page')} ${img2.canvas}, ${i18n('image')} ${idx2 + 1}`;
                tooltip.style('opacity', 1).html(pair ? `${tip}<br/>${i18n('score')}: ${pair.score.toFixed(2)}` : tip)
                    .style('left', (event.clientX + 10) + 'px').style('top', (event.clientY - 40) + 'px');
            })
            .on('mouseleave', () => tooltip.style('opacity', 0))
            .on('click', (event) => {
                const [mx, my] = d3.pointer(event, g.node());
                const idx1 = Math.floor(mx / cellSize), idx2 = Math.floor(my / cellSize);
                if (idx1 >= 0 && idx1 < images1.length && idx2 >= 0 && idx2 < images2.length) {
                    dispatch('cellclick', {idx1, idx2, mode: 'image', data: scatterData});
                }
            });

        g.selectAll('.cell').data(Array.from(pairScores.values())).join('rect')
            .attr('class', 'cell')
            .attr('x', d => d.idx1 * cellSize).attr('y', d => d.idx2 * cellSize)
            .attr('width', cellSize).attr('height', cellSize)
            .attr('fill', d3.hsl(233, 0.951, 0.52))
            .attr('opacity', d => maxScore > minScore ? 0.2 + 0.8 * (d.score - minScore) / (maxScore - minScore) : 0.5)
            .attr('pointer-events', 'none');

        container.style.width = (plotWidth + margin.left + margin.right) + 'px';
        container.style.height = (plotHeight + margin.top + margin.bottom) + 'px';
    }

    function createTooltip() {
        return d3.select('body').selectAll('.scatter-tooltip').data([0]).join('div')
            .attr('class', 'scatter-tooltip')
            .style('position', 'fixed').style('background', 'var(--bulma-scheme-main)')
            .style('border', '1px solid var(--bulma-border)').style('border-radius', '4px')
            .style('padding', '6px 10px').style('pointer-events', 'none').style('opacity', 0)
            .style('font-size', '11px').style('box-shadow', '0 2px 4px rgba(0,0,0,0.15)')
            .style('z-index', '9999').style('color', 'var(--bulma-text)');
    }

    function renderHeatmapBar(g, counts, maxCount, color, axis, height, tooltip) {
        const heatmap = g.append('g').attr('transform', axis === 'x' ? `translate(0,${-22 - height})` : 'translate(-55,0)');
        counts.forEach((count, i) => {
            if (count === 0) return;
            const rect = heatmap.append('rect')
                .attr('fill', color).attr('opacity', 0.15 + 0.85 * (count / maxCount)).style('cursor', 'default');
            if (axis === 'x') rect.attr('x', i * cellSize).attr('width', cellSize).attr('height', height);
            else rect.attr('x', 0).attr('y', i * cellSize).attr('width', height).attr('height', cellSize);
            rect.on('mouseover', () => tooltip.style('opacity', 1))
                .on('mousemove', (event) => tooltip.html(`<strong>${count}</strong> image${count > 1 ? 's' : ''}<br/>${i18n('page')} ${i + 1}`)
                    .style('left', (event.clientX + 10) + 'px').style('top', (event.clientY - 30) + 'px'))
                .on('mouseleave', () => tooltip.style('opacity', 0));
        });
    }

    function renderPageBoundaries(g, boundaries, color, axis, height, tooltip) {
        const heatmap = g.append('g').attr('transform', axis === 'x' ? `translate(0,${-22 - height})` : 'translate(-55,0)');
        boundaries.forEach(({start, end, page, count}) => {
            const rect = heatmap.append('rect').attr('fill', color).attr('opacity', 0.5).style('cursor', 'default');
            if (axis === 'x') rect.attr('x', start * cellSize).attr('width', (end - start) * cellSize).attr('height', height);
            else rect.attr('x', 0).attr('y', start * cellSize).attr('width', height).attr('height', (end - start) * cellSize);
            rect.on('mouseover', () => tooltip.style('opacity', 1))
                .on('mousemove', (event) => tooltip.html(`${i18n('page')} ${page}<br/><strong>${count}</strong> image${count > 1 ? 's' : ''}`)
                    .style('left', (event.clientX + 10) + 'px').style('top', (event.clientY - 30) + 'px'))
                .on('mouseleave', () => tooltip.style('opacity', 0));
        });
    }

    function renderAxisLabel(g, doc, plotWidth, plotHeight, axis, suffix) {
        const truncate = (text, maxPx) => { const maxChars = Math.floor(maxPx / 6); return text.length > maxChars ? text.slice(0, maxChars - 1) + '…' : text; };
        const size = axis === 'x' ? plotWidth : plotHeight;

        const label = g.append('g').attr('transform', axis === 'x'
            ? `translate(${plotWidth / 2},${-50})`
            : `translate(-68,${plotHeight / 2}) rotate(-90)`);
        label.append('circle').attr('r', 4).attr('cx', -size / 2 + 4).attr('fill', doc.color);
        label.append('text').attr('x', -size / 2 + 14).attr('text-anchor', 'start').attr('dominant-baseline', 'middle')
            .attr('font-size', '11px').attr('fill', 'var(--bulma-text)').text(truncate(`${doc.title} (${suffix})`, size - 20));
    }
</script>

<div class="scatter-container" bind:this={container}></div>

<style>
    .scatter-container {
        display: block;
    }
</style>

<script>
    import * as d3 from 'd3';
    import LegendItem from './LegendItem.svelte';

    export let documentSetStore;

    const { documentNodes, docPairStats, pairIndex, documentStats } = documentSetStore;

    let matrixContainer;
    let scatterSvg;
    let selectedCell = null;
    let sortOrder = 'name';

    $: documents = Array.from($documentNodes?.values() || []);
    $: matrixData = buildMatrix(documents, $docPairStats.scoreCount, $documentStats.scoreCount);
    $: scatterData = selectedCell ? buildScatter(selectedCell) : null;

    const cellSize = 30;
    const margin = { top: 100, right: 10, bottom: 10, left: 100 };

    function buildMatrix(docs, scoreCount, docStats) {
        if (!docs.length) return { docs: [], matrix: [], orders: {}, maxScore: 0 };

        const n = docs.length;
        const matrix = Array(n).fill(0).map(() => Array(n).fill(0));
        let maxScore = 0;

        docs.forEach((doc, i) => {
            doc.index = i;
            doc.count = docStats?.get(doc.id)?.count || 0;
        });

        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                if (i !== j) {
                    const key = docs[i].id < docs[j].id
                        ? `${docs[i].id}-${docs[j].id}`
                        : `${docs[j].id}-${docs[i].id}`;
                    const score = scoreCount?.get(key)?.score || 0;
                    if (score > maxScore) maxScore = score;
                    matrix[i][j] = { x: j, y: i, z: score };
                } else {
                    matrix[i][j] = { x: j, y: i, z: 0, diagonal: true };
                }
            }
        }

        const orders = {
            name: d3.range(n).sort((a, b) => docs[a].title.localeCompare(docs[b].title)),
            score: d3.range(n).sort((a, b) => docs[b].count - docs[a].count),
        };

        return { docs, matrix, orders, maxScore };
    }

    function buildScatter(cell) {
        const { doc1, doc2 } = cell;
        const pairKey = doc1.id < doc2.id ? `${doc1.id}-${doc2.id}` : `${doc2.id}-${doc1.id}`;
        const pairs = $pairIndex.byDocPair.get(pairKey) || [];

        if (!pairs.length) return null;

        const pageMap = new Map();
        let minScore = Infinity;
        let maxScore = -Infinity;

        pairs.forEach(p => {
            const [page1, page2, score] = p.regions_id_1 === doc1.id
                ? [p.page_1, p.page_2, p.weightedScore || 0]
                : [p.page_2, p.page_1, p.weightedScore || 0];

            const key = `${page1}-${page2}`;
            if (!pageMap.has(key)) pageMap.set(key, { page1, page2, scores: [] });

            pageMap.get(key).scores.push(score);
            if (score < minScore) minScore = score;
            if (score > maxScore) maxScore = score;
        });

        const points = Array.from(pageMap.values()).map(({ page1, page2, scores }) => ({
            page1,
            page2,
            score: scores.reduce((a, b) => a + b, 0) / scores.length,
            count: scores.length
        }));

        return { points, minScore, maxScore, doc1, doc2 };
    }

    function renderMatrix() {
        if (!matrixContainer || !matrixData.docs.length) return;

        const { docs, matrix, maxScore } = matrixData;
        const width = docs.length * cellSize;
        const height = docs.length * cellSize;

        d3.select(matrixContainer).selectAll('*').remove();

        const svg = d3.select(matrixContainer)
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const x = d3.scaleBand().range([0, width]).domain(d3.range(docs.length)).padding(0.01);

        const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('position', 'fixed')
            .style('background', 'white')
            .style('border', '1px solid #ddd')
            .style('border-radius', '4px')
            .style('padding', '8px')
            .style('pointer-events', 'none')
            .style('opacity', 0)
            .style('font-size', '12px')
            .style('box-shadow', '0 2px 4px rgba(0,0,0,0.1)')
            .style('z-index', '9999');

        const row = g.selectAll('.row')
            .data(matrix)
            .join('g')
            .attr('class', 'row')
            .attr('transform', (d, i) => `translate(0,${x(i)})`);

        row.each(function(rowData) {
            d3.select(this).selectAll('.cell')
                .data(rowData.filter(d => d.z > 0 || d.diagonal))
                .join('rect')
                .attr('class', 'cell')
                .attr('x', d => x(d.x))
                .attr('width', x.bandwidth())
                .attr('height', x.bandwidth())
                .attr('fill', d => {
                    if (d.diagonal) return '#e8e8e8';
                    const color = d3.hsl(233, 0.951, 0.52);
                    color.opacity = maxScore > 0 ? d.z / maxScore : 0;
                    return color;
                })
                .attr('stroke', '#fff')
                .attr('stroke-width', 0.5)
                .style('opacity', 0.8)
                .style('cursor', d => d.diagonal ? 'default' : 'pointer')
                .on('mouseover', function(event, d) {
                    if (d.diagonal) return;
                    d3.select(this).attr('stroke', '#000').attr('stroke-width', 2).style('opacity', 1);
                    tooltip.style('opacity', 1);
                })
                .on('mousemove', function(event, d) {
                    if (d.diagonal) return;
                    tooltip
                        .html(`<strong>${docs[d.y].title}</strong><br/>↔<br/><strong>${docs[d.x].title}</strong><br/><br/>Score: ${d.z.toFixed(2)}`)
                        .style('left', (event.clientX + 15) + 'px')
                        .style('top', (event.clientY + 15) + 'px');
                })
                .on('mouseleave', function() {
                    d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.5).style('opacity', 0.8);
                    tooltip.style('opacity', 0);
                })
                .on('click', (event, d) => {
                    if (d.diagonal) return;
                    selectedCell = { row: d.y, col: d.x, doc1: docs[d.y], doc2: docs[d.x] };
                });
        });

        updateOrder();
    }

    function renderScatter() {
        if (!scatterSvg || !scatterData?.points.length) return;

        d3.select(scatterSvg).selectAll('*').remove();

        const { points, minScore, maxScore, doc1, doc2 } = scatterData;
        const margin = { top: 40, right: 20, bottom: 60, left: 70 };
        const width = 500 - margin.left - margin.right;
        const height = 500 - margin.top - margin.bottom;

        const svg = d3.select(scatterSvg)
            .attr('width', 500)
            .attr('height', 500);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const maxPage1 = Math.max(...points.map(p => p.page1));
        const maxPage2 = Math.max(...points.map(p => p.page2));

        const xScale = d3.scaleLinear().domain([0, maxPage1]).range([0, width]);
        const yScale = d3.scaleLinear().domain([0, maxPage2]).range([height, 0]);

        g.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(xScale).ticks(Math.min(maxPage1, 10)));

        g.append('g').call(d3.axisLeft(yScale).ticks(Math.min(maxPage2, 10)));

        g.append('text')
            .attr('x', width / 2)
            .attr('y', height + 40)
            .attr('text-anchor', 'middle')
            .attr('font-size', '12px')
            .text(`${doc1.title} (page)`);

        g.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -height / 2)
            .attr('y', -50)
            .attr('text-anchor', 'middle')
            .attr('font-size', '12px')
            .text(`${doc2.title} (page)`);

        g.selectAll('.point')
            .data(points)
            .join('circle')
            .attr('cx', d => xScale(d.page1))
            .attr('cy', d => yScale(d.page2))
            .attr('r', 4)
            .attr('fill', d => {
                const color = d3.hsl(233, 0.951, 0.52);
                color.opacity = (d.score - minScore) / (maxScore - minScore);
                return color;
            })
            .attr('opacity', 0.7);
    }

    function updateOrder() {
        if (!matrixContainer || !matrixData.orders[sortOrder]) return;

        const { docs, orders } = matrixData;
        const x = d3.scaleBand().range([0, docs.length * cellSize]).domain(orders[sortOrder]).padding(0.01);

        const svg = d3.select(matrixContainer).select('svg').select('g');
        const t = svg.transition().duration(1500);

        t.selectAll('.row')
            .delay((d, i) => x(i) * 2)
            .attr('transform', (d, i) => `translate(0,${x(i)})`)
            .selectAll('.cell')
            .delay(d => x(d.x) * 2)
            .attr('x', d => x(d.x));
    }

    $: if (matrixContainer && matrixData.docs.length) renderMatrix();
    $: if (scatterSvg && scatterData) renderScatter();
    $: if (sortOrder && matrixContainer) updateOrder();
</script>

<div class="columns">
    {#if !documents.length}
        <div class="column">
            <div class="notification is-info">Aucun document disponible</div>
        </div>
    {:else}
        <div class="column is-half">
            <div class="box">
                <div class="field">
                    <label class="label" for="sort-order">Ordre</label>
                    <div class="control" id="sort-order">
                        <div class="select">
                            <select bind:value={sortOrder}>
                                <option value="name">Par nom</option>
                                <option value="score">Par score</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="matrix-wrapper">
                    <div class="row-headers">
                        {#each matrixData.docs as doc}
                            <div class="header-item" style="height: {cellSize}px;">
                                <LegendItem id={doc.id} meta={doc} onlyColor={true} clickable={false} />
                            </div>
                        {/each}
                    </div>
                    <div class="matrix-main">
                        <div class="col-headers">
                            {#each matrixData.docs as doc}
                                <div class="header-item" style="width: {cellSize}px;">
                                    <LegendItem id={doc.id} meta={doc} onlyColor={true} clickable={false} />
                                </div>
                            {/each}
                        </div>
                        <div bind:this={matrixContainer}></div>
                    </div>
                </div>
            </div>
        </div>

        {#if selectedCell}
            <div class="column is-half">
                <div class="box">
                    <h4 class="title is-5">Similarité page par page</h4>
                    <svg bind:this={scatterSvg}></svg>
                </div>
            </div>
        {/if}
    {/if}
</div>

<style>
    .matrix-wrapper {
        display: flex;
        gap: 0.5rem;
        overflow: auto;
    }

    .row-headers {
        display: flex;
        flex-direction: column;
        padding-top: 100px;
    }

    .col-headers {
        display: flex;
        margin-left: 100px;
        margin-bottom: 0.5rem;
    }

    .header-item {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .matrix-main {
        display: flex;
        flex-direction: column;
    }
</style>

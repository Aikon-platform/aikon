<script>
    import { afterUpdate } from 'svelte';
    import * as d3 from 'd3';

    export let documentSetStore;

    const { documentNodes, docPairStats, allPairs } = documentSetStore;

    let matrixContainer;
    let scatterContainer;
    let selectedCell = null;

    $: documents = Array.from($documentNodes?.values() || []).slice(0, 25);
    $: matrixData = buildMatrixData(documents, $docPairStats.scoreCount);
    $: scatterData = selectedCell ? buildScatterData(selectedCell, $allPairs) : null;

    function buildMatrixData(docs, scoreCount) {
        const matrix = [];
        let globalMax = 0;

        scoreCount.forEach(({score}) => {
            if (score > globalMax) globalMax = score;
        });

        for (let i = 0; i < docs.length; i++) {
            const row = [];
            for (let j = 0; j < docs.length; j++) {
                if (i === j) {
                    row.push({ score: globalMax, normalized: 100 }); // Diagonale = 100
                } else {
                    const {r1, r2} = {r1: docs[i].id, r2: docs[j].id};
                    const key = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
                    const stat = scoreCount.get(key);
                    const score = stat?.score || 0;
                    const normalized = globalMax > 0 ? (score / globalMax) * 100 : 0;
                    row.push({ score, normalized });
                }
            }
            matrix.push(row);
        }

        return { docs, matrix, max: globalMax };
    }

    function buildScatterData(cell, pairs) {
        const { doc1, doc2 } = cell;

        const relevantPairs = pairs.filter(p =>
            (p.regions_id_1 === doc1.id && p.regions_id_2 === doc2.id) ||
            (p.regions_id_2 === doc1.id && p.regions_id_1 === doc2.id)
        );

        if (!relevantPairs.length) return null;

        const pageMap = new Map();
        let minScore = Infinity;
        let maxScore = -Infinity;

        relevantPairs.forEach(p => {
            let page1, page2, score;

            if (p.regions_id_1 === doc1.id) {
                page1 = p.page_1;
                page2 = p.page_2;
                score = p.weightedScore || 0;
            } else {
                page1 = p.page_2;
                page2 = p.page_1;
                score = p.weightedScore || 0;
            }

            const key = `${page1}-${page2}`;
            if (!pageMap.has(key)) {
                pageMap.set(key, { page1, page2, scores: [], count: 0 });
            }

            const entry = pageMap.get(key);
            entry.scores.push(score);
            entry.count++;

            if (score < minScore) minScore = score;
            if (score > maxScore) maxScore = score;
        });

        const points = Array.from(pageMap.values()).map(({ page1, page2, scores, count }) => {
            const avgScore = scores.reduce((a, b) => a + b, 0) / count;
            return { page1, page2, score: avgScore, count };
        });

        return { points, minScore, maxScore, doc1, doc2 };
    }

    function renderMatrix(container, data) {
        if (!container || !data.docs.length) return;

        d3.select(container).selectAll('*').remove();

        const margin = { top: 100, right: 20, bottom: 20, left: 100 };
        const cellSize = 30;
        const width = data.docs.length * cellSize + margin.left + margin.right;
        const height = data.docs.length * cellSize + margin.top + margin.bottom;

        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const rows = g.selectAll('.row')
            .data(data.matrix)
            .join('g')
            .attr('class', 'row')
            .attr('transform', (d, i) => `translate(0,${i * cellSize})`);

        rows.selectAll('.cell')
            .data((d, i) => d.map((cell, j) => ({ ...cell, row: i, col: j })))
            .join('rect')
            .attr('class', 'cell')
            .attr('x', d => d.col * cellSize)
            .attr('width', cellSize)
            .attr('height', cellSize)
            .attr('fill', d => {
                const color = d3.hsl(233, 0.951, 0.52);
                color.opacity = d.normalized / 100;
                return color;
            })
            .attr('stroke', d => {
                if (selectedCell && selectedCell.row === d.row && selectedCell.col === d.col) {
                    return '#000';
                }
                return '#fff';
            })
            .attr('stroke-width', d => {
                if (selectedCell && selectedCell.row === d.row && selectedCell.col === d.col) {
                    return 4;
                }
                return 1;
            })
            .attr('stroke-opacity', d => {
                if (selectedCell && selectedCell.row === d.row && selectedCell.col === d.col) {
                    return 1;
                }
                return 0.3;
            })
            .style('cursor', 'pointer')
            .on('click', (event, d) => {
                selectedCell = {
                    row: d.row,
                    col: d.col,
                    doc1: data.docs[d.row],
                    doc2: data.docs[d.col]
                };
                renderMatrix(container, data);
            });

        g.selectAll('.label-y')
            .data(data.docs)
            .join('text')
            .attr('class', 'label-y')
            .attr('x', -5)
            .attr('y', (d, i) => i * cellSize + cellSize / 2)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'end')
            .attr('font-size', '10px')
            .text(d => {
                const label = d.title || `Doc ${d.id}`;
                return label.length > 20 ? label.substring(0, 17) + '...' : label;
            });

        g.selectAll('.label-x')
            .data(data.docs)
            .join('text')
            .attr('class', 'label-x')
            .attr('x', (d, i) => i * cellSize + cellSize / 2)
            .attr('y', -5)
            .attr('text-anchor', 'start')
            .attr('font-size', '10px')
            .attr('transform', (d, i) => `rotate(-45, ${i * cellSize + cellSize / 2}, -5)`)
            .text(d => {
                const label = d.title || `Doc ${d.id}`;
                return label.length > 20 ? label.substring(0, 17) + '...' : label;
            });
    }

    function renderScatter(container, data) {
        if (!container) return;

        d3.select(container).selectAll('*').remove();

        if (!data || !data.points.length) {
            d3.select(container)
                .append('div')
                .style('padding', '2rem')
                .style('text-align', 'center')
                .style('color', '#999')
                .text('Aucune paire de pages trouvée entre ces deux documents.');
            return;
        }

        const margin = { top: 40, right: 20, bottom: 50, left: 60 };
        const width = 500 - margin.left - margin.right;
        const height = 500 - margin.top - margin.bottom;

        const svg = d3.select(container)
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom);

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        const maxPage1 = Math.max(...data.points.map(p => p.page1), 0);
        const maxPage2 = Math.max(...data.points.map(p => p.page2), 0);

        const xScale = d3.scaleLinear()
            .domain([0, maxPage2])
            .range([0, width]);

        const yScale = d3.scaleLinear()
            .domain([0, maxPage1])
            .range([height, 0]);

        g.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(xScale)
                .ticks(Math.min(maxPage2 + 1, 10))
                .tickFormat(d3.format('d')));

        g.append('g')
            .call(d3.axisLeft(yScale)
                .ticks(Math.min(maxPage1 + 1, 10))
                .tickFormat(d3.format('d')));

        g.append('text')
            .attr('x', width / 2)
            .attr('y', height + 40)
            .attr('text-anchor', 'middle')
            .attr('font-size', '12px')
            .text(`${data.doc2.title || `Doc ${data.doc2.id}`} (page)`);

        g.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -height / 2)
            .attr('y', -40)
            .attr('text-anchor', 'middle')
            .attr('font-size', '12px')
            .text(`${data.doc1.title || `Doc ${data.doc1.id}`} (page)`);

        const scoreRange = data.maxScore - data.minScore;

        g.selectAll('.point')
            .data(data.points)
            .join('circle')
            .attr('class', 'point')
            .attr('cx', d => xScale(d.page2))
            .attr('cy', d => yScale(d.page1))
            .attr('r', 5)
            .attr('fill', d3.hsl(233, 0.951, 0.52))
            .attr('opacity', d => {
                if (scoreRange === 0) return 0.55;
                const normalized = (d.score - data.minScore) / scoreRange;
                return 0.1 + normalized * 0.9;
            });
    }

    afterUpdate(() => {
        if (matrixContainer && matrixData) {
            renderMatrix(matrixContainer, matrixData);
        }
        if (scatterContainer && scatterData) {
            renderScatter(scatterContainer, scatterData);
        }
    });
</script>

<div class="document-matrix">
    <div class="matrix-panel">
        <h3 class="title is-5">Document similarity matrix</h3>
        <div bind:this={matrixContainer} class="matrix-container"></div>
    </div>

    {#if selectedCell}
        <div class="scatter-panel">
            <h3 class="title is-5">Page similarity</h3>
            <div bind:this={scatterContainer} class="scatter-container"></div>
        </div>
    {/if}
</div>

<style>
    .document-matrix {
        display: flex;
        gap: 2rem;
        padding: 1rem;
        overflow-x: auto;
        min-height: 600px;
    }

    .matrix-panel {
        flex: 0 0 50%;
        min-width: 400px;
    }

    .scatter-panel {
        flex: 0 0 45%;
        min-width: 400px;
    }

    .matrix-container,
    .scatter-container {
        overflow: auto;
        height: 100%;
    }

    :global(.cell:hover) {
        stroke: #333 !important;
        stroke-width: 2px !important;
    }
</style>

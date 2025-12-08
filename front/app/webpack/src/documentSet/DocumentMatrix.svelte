<script>
    import * as d3 from 'd3';
    import LegendItem from './LegendItem.svelte';
    import {shorten} from "../utils.js";

    export let documentSetStore;

    const { documentNodes, docPairStats, pairIndex, selectedCategories } = documentSetStore;

    let matrixContainer;
    let scatterContainer;
    let selectedCell = null;

    $: documents = Array.from($documentNodes?.values() || []);
    $: matrixData = buildMatrixData(documents, $docPairStats.scoreCount);
    $: scatterData = selectedCell ? buildScatterData(selectedCell) : null;

    const cellSize = 30;


    // todo put that in docset store
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
                    row.push({ score: 0, normalized: 0, isDiagonal: true }); // Diagonale = 0
                } else {
                    const {r1, r2} = {r1: docs[i].id, r2: docs[j].id};
                    const key = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
                    const stat = scoreCount.get(key);
                    const score = stat?.score || 0;
                    const normalized = globalMax > 0 ? (score / globalMax) * 100 : 0;
                    row.push({ score, normalized, isDiagonal: false });
                }
            }
            matrix.push(row);
        }

        return { docs, matrix, max: globalMax };
    }

    function buildScatterData(cell) {
        const { doc1, doc2 } = cell;

        const pairKey = doc1.id < doc2.id ? `${doc1.id}-${doc2.id}` : `${doc2.id}-${doc1.id}`;
        const relevantPairs = $pairIndex.byDocPair.get(pairKey) || [];

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

            // TODO build page index inside store?

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

        const margin = { top: 10, right: 20, bottom: 20, left: 10 };
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
                if (d.isDiagonal) {
                    return '#e0e0e0'; // Couleur grise pour la diagonale
                }
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
            .domain([0, maxPage1])
            .range([0, width]);

        const yScale = d3.scaleLinear()
            .domain([0, maxPage2])
            .range([height, 0]);

        g.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(xScale)
                .ticks(Math.min(maxPage1 + 1, 10))
                .tickFormat(d3.format('d')));

        g.append('g')
            .call(d3.axisLeft(yScale)
                .ticks(Math.min(maxPage2 + 1, 10))
                .tickFormat(d3.format('d')));

        g.append('foreignObject')
            .attr('x', 0)
            .attr('y', height + 10)
            .attr('width', width)
            .attr('height', 100)
            .append('xhtml:div')
            .style('display', 'flex')
            .style('align-items', 'center')
            .style('justify-content', 'center')
            .style('gap', '0.5rem')
            .style('margin-top', '20px')
            .html(`<span class="legend-color" style="background-color: ${data.doc1.color}; width: 12px; height: 12px; display: inline-block; border-radius: 50%;"></span>
                <span style="font-size: 12px;">${shorten(data.doc1.title) || `Doc ${data.doc1.id}`} (page)</span>`);

        g.append('foreignObject')
            .attr('x', -margin.left + 5)
            .attr('y', 0)
            .attr('width', 50)
            .attr('height', width)
            .append('xhtml:div')
            .style('display', 'flex')
            .style('align-items', 'center')
            .style('justify-content', 'center')
            .style('gap', '0.5rem')
            .style('transform', `rotate(-90deg) translateX(-${height/2}px)`)
            .style('transform-origin', 'left top')
            .style('white-space', 'nowrap')
            //.style('height', '100%')
            .html(`<span class="legend-color" style="background-color: ${data.doc2.color}; width: 12px; height: 12px; display: inline-block; border-radius: 50%;"></span>
                <span style="font-size: 12px;">${shorten(data.doc2.title) || `Doc ${data.doc2.id}`} (page)</span>`);

        const scoreRange = data.maxScore - data.minScore;

        g.selectAll('.point')
            .data(data.points)
            .join('rect')
            .attr('class', 'point')
            .attr('x', d => xScale(d.page1) - 4)
            .attr('y', d => yScale(d.page2) - 4)
            .attr('width', 8)
            .attr('height', 8)
            .attr('fill', d3.hsl(233, 0.951, 0.52))
            .attr('opacity', d => {
                const categories = $selectedCategories || [];
                if (categories.length === 1 && categories[0] === 1) {
                    return 1;
                }
                return opacity(d.score, {min: data.minScore, max: data.maxScore, range: scoreRange});
            });
    }

    function opacity(score, scoreRange, minOpacity = 0.05, maxOpacity = 1) {
        const {min, _, range} = scoreRange;
        if (range === 0) return 0.55;
        return minOpacity + Math.pow((score - min) / range, 3) * maxOpacity;
    }

    $: if (scatterContainer && scatterData) {
        renderScatter(scatterContainer, scatterData);
    }

    $: if (matrixContainer && matrixData) {
        renderMatrix(matrixContainer, matrixData);
    }
</script>

<div class="document-matrix columns">
    {#if !documents.length}
        <div class="notification is-info">
            Aucun document disponible pour afficher la matrice de similarité.
        </div>
    {:else}
        <div class="matrix-panel column">
            <h3 class="title is-5">Similarity Matrix</h3>
            <div class="matrix-wrapper">
                <div class="matrix-content">
                    <div class="row-headers">
                        {#each documents as doc, i}
                            <div class="row-header" style="height: {cellSize}px; line-height: {cellSize}px;">
                                <LegendItem id={doc.id} meta={doc} onlyColor={true} clickable={false} />
                            </div>
                        {/each}
                    </div>
                    <div bind:this={matrixContainer} class="matrix-container"></div>
                </div>
            </div>
        </div>

        {#if selectedCell}
            <div class="scatter-panel column">
                <h3 class="title is-5">Page-by-page similarity</h3>
                <div bind:this={scatterContainer} class="scatter-container"></div>
            </div>
        {/if}
    {/if}
</div>

<style>
    .document-matrix {
        display: flex;
        gap: 2rem;
        padding: 1rem;
        overflow-x: auto;
        min-height: 90vh;
    }

    .scatter-container {
        height: 100%;
    }

    .matrix-panel {
        flex: 0 0 50%;
        min-width: 400px;
    }

    .scatter-panel {
        flex: 0 0 45%;
        min-width: 400px;
    }

    .matrix-wrapper {
        display: flex;
        flex-direction: column;
    }

    .matrix-content {
        display: flex;
        align-items: flex-start;
    }

    .row-headers {
        display: flex;
        flex-direction: column;
        margin-right: 0.5rem;
        flex-shrink: 0;
    }

    .row-header {
        display: flex;
        align-items: center;
        justify-content: center;
        padding-top: 20px;
    }

    .matrix-container {
        flex: 1;
    }

    .scatter-container {
        overflow: auto;
    }

    :global(.cell:hover) {
        stroke: #333 !important;
        stroke-width: 2px !important;
    }
</style>

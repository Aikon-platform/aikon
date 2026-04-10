<script>
    import * as d3 from "d3";
    import {createEventDispatcher} from "svelte";
    import {i18n} from "../../utils.js";

    export let documents = [];
    export let scoreData = new Map();
    export let docStats = new Map();
    export let imageCountMap = new Map();
    export let normalize = true;
    export let sortOrder = "name";
    export let cellSize = 30;
    export let percentageMode = false;
    export let coverageData = new Map();

    const dispatch = createEventDispatcher();

    const t = {
        score: {en: "Score", fr: "Score"},
        noPairs: {en: "No pairs", fr: "Aucune paire"},
    };

    let container;
    let selectedCell = null;

    $: matrixData = buildMatrix(documents, scoreData, docStats, sortOrder, normalize, imageCountMap, percentageMode, coverageData);

    function buildMatrix(docs, scoreCount, docStatsMap, order, doNormalize, imgCount, pctMode, coverage) {
        if (!docs.length) return {docs: [], matrix: [], maxScore: 0};

        docs.forEach((doc, i) => {
            doc.index = i;
            doc.count = docStatsMap?.get(doc.id)?.count || 0;
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

                    let z, pct;

                    if (pctMode) {
                        const covKey = `${sorted[i].id}-${sorted[j].id}`;
                        const covCount = coverage.get(covKey)?.size || 0;
                        const total = imgCount.get(sorted[i].id) || 1;
                        pct = covCount / total;
                        z = pct;
                    } else {
                        let score = scoreCount?.get(key)?.score || 0;
                        if (doNormalize && score > 0) {
                            const n1 = imgCount.get(sorted[i].id) || 1;
                            const n2 = imgCount.get(sorted[j].id) || 1;
                            score /= Math.sqrt(n1 * n2);
                        }
                        z = score;
                    }

                    if (z > maxScore) maxScore = z;
                    row.push({x: j, y: i, z, pct, doc1: sorted[i], doc2: sorted[j]});
                } else {
                    row.push({x: j, y: i, z: 0, diagonal: true});
                }
            }
            matrix.push(row);
        }

        return {docs: sorted, matrix, maxScore, pctMode};
    }

    function isSelected(d) {
        return selectedCell && selectedCell.doc1.id === d.doc1.id && selectedCell.doc2.id === d.doc2.id;
    }

    function render() {
        if (!container || !matrixData.docs.length) return;

        const {docs, matrix, maxScore} = matrixData;
        const size = docs.length * cellSize;

        d3.select(container).selectAll("*").remove();

        const svg = d3.select(container)
            .append("svg")
            .attr("width", size)
            .attr("height", size);

        const x = d3.scaleBand().range([0, size]).domain(d3.range(docs.length)).padding(0.02);

        const tooltip = d3.select("body").selectAll(".matrix-tooltip").data([0])
            .join("div")
            .attr("class", "matrix-tooltip")
            .style("position", "fixed")
            .style("background", "var(--bulma-scheme-main)")
            .style("border", "1px solid var(--bulma-border)")
            .style("border-radius", "4px")
            .style("padding", "8px")
            .style("pointer-events", "none")
            .style("opacity", 0)
            .style("font-size", "12px")
            .style("box-shadow", "0 2px 4px rgba(0,0,0,0.15)")
            .style("z-index", "9999")
            .style("color", "var(--bulma-text)");

        const row = svg.selectAll(".row")
            .data(matrix)
            .join("g")
            .attr("class", "row")
            .attr("transform", (d, i) => `translate(0,${x(i)})`);

        row.each(function (rowData) {
            const cells = d3.select(this).selectAll(".cell")
                .data(rowData.filter(d => !d.diagonal))
                .join("rect")
                .attr("class", "cell")
                .attr("x", d => x(d.x))
                .attr("width", x.bandwidth())
                .attr("height", x.bandwidth())
                .attr("fill", d => {
                    if (d.z === 0) return "var(--bulma-text)";
                    const color = d3.hsl(233, 0.951, 0.52);
                    color.opacity = maxScore > 0 ? 0.2 + 0.8 * (d.z / maxScore) : 0.2;
                    return color;
                })
                .attr("stroke", d => isSelected(d) ? "var(--bulma-text)" : "var(--bulma-scheme-main)")
                .attr("stroke-width", d => isSelected(d) ? 2 : 0.5)
                .style("cursor", "pointer")
                .on("mouseover", function (event, d) {
                    if (!isSelected(d)) d3.select(this).attr("stroke", "var(--bulma-text)").attr("stroke-width", 2);
                    tooltip.style("opacity", 1);
                })
                .on("mousemove", function (event, d) {
                    let content;
                    if (matrixData.pctMode) {
                        const pctStr = d.pct != null ? `${(d.pct * 100).toFixed(1)}%` : "0%";
                        content = `Percentage of images from<br/><span style="color:${d.doc1.color}">●</span> ${d.doc1.title}<br/>present also in<br/><span style="color:${d.doc2.color}">●</span> ${d.doc2.title}<br/><br/><strong>${pctStr}</strong>`;
                    } else {
                        const docs = `<span style="color:${d.doc1.color}">●</span> ${d.doc1.title}<br/>↔<br/><span style="color:${d.doc2.color}">●</span> ${d.doc2.title}`;
                        content = d.z === 0
                            ? `${docs}<br/><br/><em>${i18n("noPairs", t)}</em>`
                            : `${docs}<br/><br/>${i18n("score", t)}: ${d.z.toFixed(2)}`;
                    }
                    tooltip.html(content)
                        .style("left", (event.clientX + 15) + "px")
                        .style("top", (event.clientY + 15) + "px");
                })
                .on("mouseleave", function (event, d) {
                    if (!isSelected(d)) d3.select(this).attr("stroke", "var(--bulma-scheme-main)").attr("stroke-width", 0.5);
                    tooltip.style("opacity", 0);
                })
                .on("click", (event, d) => {
                    selectedCell = {row: d.y, col: d.x, doc1: d.doc1, doc2: d.doc2};
                    updateSelection();
                    dispatch("cellselect", selectedCell);
                });

            if (matrixData.pctMode) {
                d3.select(this).selectAll(".cell-label")
                    .data(rowData.filter(d => !d.diagonal && d.pct > 0))
                    .join("text")
                    .attr("class", "cell-label")
                    .attr("x", d => x(d.x) + x.bandwidth() / 2)
                    .attr("y", x.bandwidth() / 2)
                    .attr("text-anchor", "middle")
                    .attr("dominant-baseline", "central")
                    .attr("font-size", Math.min(x.bandwidth() * 0.35, 10) + "px")
                    .attr("fill", "white")
                    .attr("pointer-events", "none")
                    .text(d => `${Math.round(d.pct * 100)}%`);
            }
        });

        svg.selectAll(".row").selectAll(".cell-diagonal")
            .data(d => d.filter(c => c.diagonal))
            .join("rect")
            .attr("class", "cell-diagonal")
            .attr("x", d => x(d.x))
            .attr("width", x.bandwidth())
            .attr("height", x.bandwidth())
            .attr("fill", "var(--contrasted)");
    }

    function updateSelection() {
        if (!container) return;
        d3.select(container).selectAll(".cell")
            .attr("stroke", d => isSelected(d) ? "var(--bulma-text)" : "var(--bulma-scheme-main)")
            .attr("stroke-width", d => isSelected(d) ? 2 : 0.5);
    }

    export function clearSelection() {
        selectedCell = null;
        updateSelection();
    }

    $: if (container && matrixData.docs.length) render();
</script>

<div class="matrix-grid" style="--cell-size: {cellSize}px;">
    <div class="matrix-corner"></div>
    {#each ["col", "row"] as side}
        <div class="{side}-headers">
            {#each matrixData.docs as doc (doc.id)}
                <div class="header-cell">
                    <span class="color-dot" style="background-color: {doc.color}" title="{doc.title} {i18n('Witness')} #{doc.witness_id}"></span>
                </div>
            {/each}
        </div>
    {/each}
    <div class="matrix-canvas" bind:this={container}></div>
</div>

<style>
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
</style>

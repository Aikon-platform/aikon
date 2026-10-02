<script context="module">
    export const viewModes = {
        matches: {en: "By matches", fr: "Par correspondances"},
        score: {en: "By score", fr: "Par score"},
        percentage: {en: "By percentage", fr: "Par pourcentage"},
    };
</script>
<script>
    import * as d3 from "d3";
    import {createEventDispatcher} from "svelte";
    import {i18n} from "../../utils.js";
    import RightClick from "../../ui/RightClick.svelte";

    export let documents = [];
    export let scoreData = new Map();
    export let docStats = new Map();
    export let imageCountMap = new Map();
    export let normalize = true;
    export let cellSize = 30;
    export let mode = "matches";
    export let coverageData = new Map();

    export let isInStemma = false;
    export let stemmaStore = null;

    const matchLevel = d3.scaleThreshold([1, 11, 26, 51], [0, 0, 1 / 3, 2 / 3, 1]);
    const cellLabel = {
        matches: d => d.count,
        score: d => d.ratio.toFixed(1),
        percentage: d => `${Math.round(d.pct * 100)}%`,
    };

    $: edges = stemmaStore?.edges;
    $: edgeKeys = isInStemma && $edges
        ? new Set($edges.map(e => e.source < e.target ? `${e.source}-${e.target}` : `${e.target}-${e.source}`))
        : new Set();
    $: if (container && matrixData.docs.length) { edgeKeys; render(); }

    const dispatch = createEventDispatcher();

    const t = {
        score: {en: "Score", fr: "Score"},
        match: {en: "matches", fr: "correspondances"},
        noPairs: {en: "No pairs", fr: "Aucune paire"},
        addEdge: {en: "Add stemma edge", fr: "Ajouter un lien au stemma"},
        percent: {en: "Percentage of images from", fr: "Pourcentage des images issues de"},
        present: {en: "also present in", fr: "aussi présentes dans"},
        rank: {
            en: "{x} × the median score of document pairs with matches",
            fr: "{x} × le score médian des paires de documents comportant des correspondances"
        },
    };

    let container;
    let selectedCell = null;

    $: matrixData = buildMatrix(documents, scoreData, docStats, normalize, imageCountMap, mode, $coverageData);

    function buildMatrix(docs, scoreCount, docStatsMap, doNormalize, imgCount, mode, coverage) {
        if (!docs.length) return {docs: [], matrix: [], maxScore: 0};

        docs.forEach((doc, i) => {
            doc.index = i;
            doc.count = docStatsMap?.get(doc.id)?.count || 0;
        });

        const n = docs.length;
        const matrix = [];
        const scores = [];
        let maxScore = 0;

        for (let i = 0; i < n; i++) {
            const row = [];
            for (let j = 0; j < n; j++) {
                if (i !== j) {
                    const id1 = docs[i].id, id2 = docs[j].id;
                    const entry = scoreCount?.get(id1 < id2 ? `${id1}-${id2}` : `${id2}-${id1}`);
                    const n1 = imgCount.get(id1) || 1;
                    const count = entry?.matchCount || 0;
                    let score = entry?.matchScore || 0;
                    if (doNormalize && score) score /= Math.sqrt(n1 * (imgCount.get(id2) || 1));
                    const pct = (coverage.get(`${id1}-${id2}`)?.size || 0) / n1;
                    const z = mode === "matches" ? count : mode === "score" ? score : pct;

                    if (z > maxScore) maxScore = z;
                    if (i < j && score) scores.push(score);
                    row.push({x: j, y: i, z, score, pct, count, doc1: docs[i], doc2: docs[j]});
                } else {
                    row.push({x: j, y: i, z: 0, diagonal: true});
                }
            }
            matrix.push(row);
        }

        // const sorted = Float64Array.from(scores).sort();
        // for (const row of matrix) for (const d of row) {
        //     if (d.score) d.rank = Math.round(100 * d3.bisectRight(sorted, d.score) / sorted.length);
        // }
        const median = d3.median(scores);
        for (const row of matrix) for (const d of row) {
            if (d.score) d.ratio = d.score / median;
        }

        return {docs, matrix, maxScore, mode};
    }

    function isSelected(d) {
        return selectedCell && selectedCell.doc1.id === d.doc1.id && selectedCell.doc2.id === d.doc2.id;
    }

    function isMirror(d) {
        return selectedCell && selectedCell.doc1.id === d.doc2.id && selectedCell.doc2.id === d.doc1.id;
    }

    function applyStroke(sel) {
        sel.attr("stroke", d => isSelected(d) || isMirror(d) ? "var(--bulma-text)" : "var(--bulma-scheme-main)")
            .attr("stroke-width", d => isSelected(d) || isMirror(d) ? 2 : 0.5)
            .attr("stroke-dasharray", d => isMirror(d) ? "5,2" : null);
    }

    function render() {
        if (!container || !matrixData.docs.length) return;

        const {docs, matrix, maxScore, mode} = matrixData;
        const level = d => mode === "matches" ? matchLevel(d.z) : d.z / maxScore;
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
                    const key = d.doc1.id < d.doc2.id ? `${d.doc1.id}-${d.doc2.id}` : `${d.doc2.id}-${d.doc1.id}`;
                    const color = d3.hsl(edgeKeys.has(key) ? 19 : 233, 0.951, 0.52);
                    color.opacity = 0.2 + 0.8 * level(d);
                    return color;
                })
                .call(applyStroke)
                .style("cursor", "pointer")
                .on("mouseover", function (event, d) {
                    if (!isSelected(d) && !isMirror(d)) d3.select(this).attr("stroke", "var(--bulma-text)").attr("stroke-width", 2);
                    tooltip.style("opacity", 1);
                })
                .on("mousemove", function (event, d) {
                    let content;
                    if (mode === "percentage") {
                        const pctStr = `${(d.pct * 100).toFixed(1)}%`;
                        content = `${i18n("percent", t)}<br/><span style="color:${d.doc1.color}">●</span> ${d.doc1.title}<br/>${i18n("present", t)}<br/><span style="color:${d.doc2.color}">●</span> ${d.doc2.title}<br/><br/><strong>${pctStr}</strong>`;
                    } else {
                        const docs = `<span style="color:${d.doc1.color}">●</span> ${d.doc1.title}<br/>↔<br/><span style="color:${d.doc2.color}">●</span> ${d.doc2.title}`;
                        const info = mode === "score"
                            ? `<br/>${i18n("rank", t).replace("{x}", `<b>${d.ratio.toFixed(1)}</b>`)}`
                            : ` | <b>${d.count}</b> ${i18n("match", t)}`;
                        content = !d.count
                            ? `${docs}<br/><br/><em>${i18n("noPairs", t)}</em>`
                            : `${docs}<br/><br/>${i18n("score", t)}: ${d.score.toFixed(2)}${info}`;
                    }
                    tooltip.html(content)
                        .style("left", (event.clientX + 15) + "px")
                        .style("top", (event.clientY + 15) + "px");
                })
                .on("mouseleave", function (event, d) {
                    if (!isSelected(d) && !isMirror(d)) d3.select(this).attr("stroke", "var(--bulma-scheme-main)").attr("stroke-width", 0.5);
                    tooltip.style("opacity", 0);
                })
                .on("click", (event, d) => {
                    selectedCell = {row: d.y, col: d.x, doc1: d.doc1, doc2: d.doc2};
                    updateSelection();
                    dispatch("cellselect", selectedCell);
                })
                .on("contextmenu", (event, d) => {
                    if (isInStemma && stemmaStore) openContextMenu(event, d);
                });

            d3.select(this).selectAll(".cell-label")
                .data(rowData.filter(d => !d.diagonal && d.z > 0))
                .join("text")
                .attr("class", "cell-label")
                .attr("x", d => x(d.x) + x.bandwidth() / 2)
                .attr("y", x.bandwidth() / 2)
                .attr("text-anchor", "middle")
                .attr("dominant-baseline", "central")
                .attr("font-size", Math.min(x.bandwidth() * 0.35, 10) + "px")
                .attr("fill", "white")
                .attr("pointer-events", "none")
                .text(cellLabel[mode]);
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
        applyStroke(d3.select(container).selectAll(".cell"));
    }

    export function clearSelection() {
        selectedCell = null;
        updateSelection();
    }

    $: if (container && matrixData.docs.length) render();

    let menuOpen = false, menuX = 0, menuY = 0, menuItems = [];

    function docDate(d) {
        return d.min_date ?? d.max_date ?? null;
    }

    function orientEdge(doc1, doc2) {
        const d1 = docDate(doc1), d2 = docDate(doc2);
        if (d1 != null && d2 != null) return d1 <= d2 ? [doc1, doc2] : [doc2, doc1];
        if (d1 != null) return [doc1, doc2];
        if (d2 != null) return [doc2, doc1];
        return [doc1, doc2];
    }

    function openContextMenu(event, d) {
        event.preventDefault();
        const [src, tgt] = orientEdge(d.doc1, d.doc2);
        menuItems = [{
            label: i18n("addEdge", t),
            icon: "arrow-right",
            action: () => stemmaStore.addEdge(src.id, tgt.id, src, tgt)
        }];
        menuX = event.clientX;
        menuY = event.clientY;
        menuOpen = true;
    }
</script>

<div id="doc-set-matrix" class="matrix-grid" style="--cell-size: {cellSize}px;">
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

<RightClick bind:open={menuOpen} x={menuX} y={menuY} items={menuItems}/>

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

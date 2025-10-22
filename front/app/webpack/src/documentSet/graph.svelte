<script>
    import * as d3 from 'd3';
    import {createEventDispatcher} from 'svelte';

    import { createDocumentSetStore } from "./documentSetStore.js";
    const docSetStore = createDocumentSetStore();
    const { regionMetadata } = docSetStore;

    export let data = null;
    export let corpus = null;
    export let type = "regions";

    let container;

    // 1. createLegend
    // const colorScale = d3.scaleOrdinal(generateColors(regionCount));
    // createLegend('regions-info', nodesArray, colorScale, corpus);

    // todo const regionConnections = new Map();
    // todo and const regionImages = new Map();
    // todo and imageIndex = new Map();
    // const regionCount = Object.values(corpus).reduce((count, wit) =>
    //         count + Object.keys(wit).length, 0
    //     );
    // dans store
    // aussi faire que colorScale ce soit accessible de store

    // TODO faire que updateSelection embed son imageContainer

    function processSelection(nodes, selected, order) {
        if (type === "regions"){
            return nodes.filter(d => selected.has(d.id))
        }
        return order;
    }

    export function createNetwork(div, nodes, links, updateSelection) {
        const width = 954;
        const height = 600;

        const linkStrengthScale = d3.scaleLinear()
            .domain([1, d3.max(links, d => d.count)])
            .range([0.3, 1]);

        const linkDistanceScale = d3.scaleLinear()
            .domain([1, d3.max(links, d => d.count)])
            .range([200, 50]);

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id)
                .distance(d => linkDistanceScale(d.count))
                .strength(d => linkStrengthScale(d.count))
            )
            .force("charge", d3.forceManyBody().strength(-750))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(25));

        const container = d3.select(div);

        const clickMode = "<span class='icon px-4'><i class='fas fa-hand-pointer'></i></span> Switch to click mode"
        const selectMode = "<span class='icon px-4'><i class='fas fa-crop-alt'></i></span> Switch to selection mode"

        const toggleButton = container.append("button")
            .attr("class", "toggle-button button is-small is-link")
            .html(selectMode);

        const svg = container.append("svg")
            .attr("class", "network-svg")
            .attr("width", width).attr("height", height)
            .attr("viewBox", [0, 0, width, height]);

        const g = svg.append("g");

        const selectionDiv = container.append("div")
            .attr("class", "selection-panel");

        selectionDiv.append("h3").attr("class", "title is-5")
            .text("Selected Nodes");
            // MATRIX
            //.text("Selected Witnesses");

        const selectionManager = createSelectionManager({
            svg,
            g,
            nodes: nodes,
            onSelectionChange: (selected, order) => {
                node.classed("selected", d => selected.has(d.id));
                updateSelection(processSelection(nodes, selected, order), selectionDiv);
            }
        });

        toggleButton.on("click", function () {
            const active = selectionManager.toggleSelectionMode();
            d3.select(this)
                .html(active ? clickMode : selectMode)
                .classed("active", active);
        });

        svg.call(d3.zoom()
            .scaleExtent([0.1, 10])
            .filter(() => !selectionManager.isSelectionMode())
            .on("zoom", ({transform}) => g.attr("transform", transform)));

        const link = g.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("class", "link")
            .attr("stroke-width", d => d.width);

        const node = g.append("g")
            .selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("class", "node")
            .attr("r", 32)
            .attr("fill", d => d.color);

        // TODO improve labels
        node.append("title")
            .text(d => `Region: ${d.regionId}\nPage: ${d.page}`);

        const {dragstarted, dragged, dragended} = createSimulationHandlers(simulation, link, node, label);

        selectionManager.setupNodeClick(node);
        selectionManager.setupDrag(node, {
            start: dragstarted,
            drag: dragged,
            end: dragended
        });
    }
</script>

<div class="box">
    <h2 class="title is-3 has-text-link">
        {type === "regions" ? "Images network" : "Witness network"}
    </h2>

    <div bind:this={container} class="visualization-container">
        {#if !data}
            <progress class="progress is-link" max="100">Loading...</progress>
        {/if}
    </div>
</div>

<style>
    .visualization-container {
        min-height: 600px;
    }
</style>

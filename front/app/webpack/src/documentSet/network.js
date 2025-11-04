import * as d3 from 'd3';

function createSelectionManager(options) {
    const {
        svg,
        g,
        nodes,
        onSelectionChange,
        getNodePosition = d => ({x: d.x, y: d.y}),
        getNodeId = d => d.id
    } = options;

    const selectedNodes = new Set();
    const selectionOrder = [];
    let selectionMode = false;


    function toggleSelectionMode() {
        selectionMode = !selectionMode;
        svg.style("cursor", selectionMode ? "crosshair" : "default");
        return selectionMode;
    }

    function toggleNode(nodeId) {
        if (selectedNodes.has(nodeId)) {
            selectedNodes.delete(nodeId);
            const index = selectionOrder.indexOf(nodeId);
            if (index > -1) selectionOrder.splice(index, 1);
        } else {
            selectedNodes.add(nodeId);
            selectionOrder.push(nodeId);
        }
        onSelectionChange(selectedNodes, selectionOrder);
    }

    function clearSelection() {
        selectedNodes.clear();
        selectionOrder.length = 0;
        onSelectionChange(selectedNodes, selectionOrder);
    }

    let selectionStart = null;
    let selectionRect = null;
    svg.on("mousedown", function (event) {
        if (!selectionMode) return;
        event.preventDefault();

        const [x, y] = d3.pointer(event, g.node());
        selectionStart = {x, y};
        selectionRect = g.append("rect")
            .attr("class", "selection-rect")
            .attr("x", x)
            .attr("y", y)
            .attr("width", 0)
            .attr("height", 0);
    }).on("mousemove", function (event) {
        if (!selectionMode || !selectionRect) return;

        const [x, y] = d3.pointer(event, g.node());
        const width = x - selectionStart.x;
        const height = y - selectionStart.y;

        selectionRect
            .attr("x", width < 0 ? x : selectionStart.x)
            .attr("y", height < 0 ? y : selectionStart.y)
            .attr("width", Math.abs(width))
            .attr("height", Math.abs(height));
    }).on("mouseup", function (event) {
        if (!selectionMode || !selectionRect) return;

        const [x, y] = d3.pointer(event, g.node());
        const x1 = Math.min(selectionStart.x, x);
        const y1 = Math.min(selectionStart.y, y);
        const x2 = Math.max(selectionStart.x, x);
        const y2 = Math.max(selectionStart.y, y);

        selectedNodes.clear();
        selectionOrder.length = 0;

        const newNodes = [];
        nodes.forEach(d => {
            const pos = getNodePosition(d);
            if (pos.x >= x1 && pos.x <= x2 && pos.y >= y1 && pos.y <= y2) {
                newNodes.push(getNodeId(d));
            }
        });

        newNodes.sort((a, b) => a - b);
        newNodes.forEach(id => {
            selectedNodes.add(id);
            selectionOrder.push(id);
        });

        onSelectionChange(selectedNodes, selectionOrder);

        selectionRect.remove();
        selectionRect = null;
        selectionStart = null;
    });

    return {
        toggleSelectionMode,
        toggleNode,
        clearSelection,
        isSelectionMode: () => selectionMode,
        getSelectedNodes: () => selectedNodes,
        getSelectionOrder: () => selectionOrder,
        setupNodeClick: (nodeSelection) => {
            nodeSelection.on("click", function (event, d) {
                event.stopPropagation();
                toggleNode(getNodeId(d));
            });
        },
        setupDrag: (nodeSelection, dragFunctions) => {
            nodeSelection.call(
                d3.drag()
                    .filter(() => !selectionMode)
                    .on("start", dragFunctions.start)
                    .on("drag", dragFunctions.drag)
                    .on("end", dragFunctions.end)
            );
        }
    };
}

function createSimulationHandlers(simulation, link, node, label) {
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node.attr("cx", d => d.x).attr("cy", d => d.y);
        // if (label){
        //     label.attr("x", d => d.x).attr("y", d => d.y);
        // }
    });

    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }

    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }

    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }

    return {dragstarted, dragged, dragended};
}

// TODO 1. createLegend
// const colorScale = d3.scaleOrdinal(generateColors(regionCount));
// createLegend('regions-info', nodesArray, colorScale, corpus);

// const regionCount = Object.values(corpus).reduce((count, wit) =>
//         count + Object.keys(wit).length, 0
//     );
// dans store
// aussi faire que colorScale ce soit accessible de store

function processSelection(nodes, selected, order) {
    return nodes.filter(d => selected.has(d.id));
}

export function createNetwork(div, nodes, links, onSelectionChange) {
    const width = 954;
    const height = 600;
    const centerX = width / 2;
    const centerY = height / 2;

    nodes.forEach(node => {
        node.x = centerX;
        node.y = centerY;
    });

    const linkStrengthScale = d3.scaleLinear()
        .domain([1, d3.max(links, d => d.count) || 1])
        .range([0.3, 1]);

    const linkDistanceScale = d3.scaleLinear()
        .domain([1, d3.max(links, d => d.count) || 1])
        .range([200, 50]);

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id)
            .distance(d => linkDistanceScale(d.count || 1))
            .strength(d => linkStrengthScale(d.count || 1))
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

    const selectionManager = createSelectionManager({
        svg,
        g,
        nodes: nodes,
        onSelectionChange: (selected, order) => {
            node.classed("selected", d => selected.has(d.id));
            const selectedNodesArray = processSelection(nodes, selected, order);
            onSelectionChange(selectedNodesArray);
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
    node.append("title").text(d => `Region: ${d.regionId}\nPage: ${d.page}`);

    const {dragstarted, dragged, dragended} = createSimulationHandlers(simulation, link, node, null);

    selectionManager.setupNodeClick(node);
    selectionManager.setupDrag(node, {
        start: dragstarted,
        drag: dragged,
        end: dragended
    });
    return {
        destroy: () => {
            simulation.stop();
            svg.remove();
        }
    };
}

// function createLegend(containerId, nodesArray, colorScale) {
//     const container = d3.select(`#${containerId}`);
//     container.html('');
//
//     const regionIds = [...new Set(nodesArray.map(d => d.regionId))].sort((a, b) => a - b);
//
//     const legend = container.append('div')
//         .attr('class', 'box');
//
//     legend.append('h3')
//         .attr('class', 'title is-6')
//         .text('Region Extractions');
//
//     const list = legend.append('div')
//         .attr('class', 'legend-list');
//
//     regionIds.forEach(regionId => {
//         const metadata = $regionMetadata.get(regionId);
//         if (!metadata) return;
//
//         const item = list.append('div')
//             .attr('class', 'legend-item');
//
//         item.append('span')
//             .attr('class', 'legend-color')
//             .style('background-color', colorScale(regionId));
//
//         item.append('span')
//             .attr('class', 'legend-label')
//             .html(`<a href="${BASE_URL}vhs/witness/${metadata.witnessId}/regions/${regionId}" target="_blank">${metadata.witTitle}</a>`);
//     });
// }

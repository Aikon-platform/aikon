import * as d3 from 'd3';

function calculateLinkStrength(link, scoreRange) {
    let baseScore = link.score != null ? link.score : 0;

    if (scoreRange.max > scoreRange.min) {
        baseScore = (baseScore - scoreRange.min) / (scoreRange.max - scoreRange.min);
    }

    let strength = baseScore;

    if (link.category === 1) { // exact match
        strength = baseScore + 1.0;
    } else if (link.category === 2) { // partial match
        strength = baseScore + 0.5;
    } else if (link.category === 3 || link.category === 5) { // partial and user match
        strength = baseScore + 0.125;
    } else if (link.category === 4) { // no match
        strength = Math.max(0.01, baseScore - 1.0);
    }

    return Math.max(0.01, Math.min(strength, 2));
}

function calculateLinkDistance(strength) {
    return 30 + (2 - strength) * 100;
}

function normalizeRadius(scoreSum, minSum, maxSum, minRadius = 10, maxRadius = 75) {
    if (maxSum === minSum) return (minRadius + maxRadius) / 2;
    return minRadius + ((scoreSum - minSum) / (maxSum - minSum)) * (maxRadius - minRadius);
}

function normalizeLinkStrength(scoreSum, minSum, maxSum) {
    if (maxSum === minSum) return 0.5;
    return 0.1 + ((scoreSum - minSum) / (maxSum - minSum)) * 0.9;
}

function initializeImageNetwork(nodes, links, stats) {
    links.forEach(link => {
        link.strength = calculateLinkStrength(link, stats.scoreRange);
        link.distance = calculateLinkDistance(link.strength);
    });

    nodes.forEach(node => {
        const imgStats = stats.imageStats.get(node.id) || {score: 0, count: 0};
        node.scoreSum = imgStats.score;
        node.degree = imgStats.count;
        node.radius = normalizeRadius(imgStats.score, stats.scoreSumRange.min, stats.scoreSumRange.max);
    });
}

function initializeDefaultNetwork(nodes, links) {
    links.forEach(link => {
        link.strength = 0.5;
        link.distance = 150;
    });

    nodes.forEach(node => {
        node.radius = 32;
        node.degree = 0;
    });
}

function initializeDocumentNetwork(nodes, links, stats) {
    nodes.forEach(node => {
        node.radius = normalizeRadius(
            node.imageCount,
            stats.imageCountRange.min,
            stats.imageCountRange.max,
            15,
            60
        );
    });

    links.forEach(link => {
        link.strength = normalizeLinkStrength(
            link.scoreSum,
            stats.scoreSumRange.min,
            stats.scoreSumRange.max
        );
        link.distance = calculateLinkDistance(link.strength);
    });
}

export function createNetwork(div, nodes, links, stats = null, onSelectionChange, onModeChange = null, type = 'image') {
    const width = 954;
    const height = 600;
    const centerX = width / 2;
    const centerY = height / 2;

    nodes.forEach(node => {
        node.x = centerX;
        node.y = centerY;
    });

    const validLinks = links.filter(link => link.category !== 4);

    if (type === 'image' && stats?.scoreRange) {
        initializeImageNetwork(nodes, validLinks, stats);
    } else if (type === 'document' && stats?.imageCountRange) {
        initializeDocumentNetwork(nodes, validLinks, stats);
    } else {
        initializeDefaultNetwork(nodes, validLinks);
    }

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(validLinks).id(d => d.id)
            .distance(d => d.distance)
            .strength(d => d.strength * 0.7)
        )
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(centerX, centerY).strength(0.1))
        .force("collision", d3.forceCollide().radius(d => d.radius + 3))
        .force("x", d3.forceX(centerX).strength(0.05))
        .force("y", d3.forceY(centerY).strength(0.05));

    const container = d3.select(div);

    const svg = container.append("svg")
        .attr("class", "network-svg")
        .attr("width", width).attr("height", height)
        .attr("viewBox", [0, 0, width, height]);

    const g = svg.append("g");

    const link = g.append("g")
        .selectAll("line")
        .data(validLinks)
        .join("line")
        .attr("class", "link")
        .attr("stroke-width", d => Math.max(0.5, d.strength * 2))
        .attr("stroke-opacity", d => Math.max(0.2, d.strength * 0.5));

    const node = g.append("g")
        .selectAll("circle")
        .data(nodes)
        .join("circle")
        .attr("class", "node")
        .attr("r", d => d.radius)
        .attr("fill", d => d.color);

    node.append("title").text(d => {
        let text = `Region: ${d.regionId}\nPage: ${d.canvas || d.page}`;
        if (d.degree) text += `\nConnections: ${d.degree}`;
        if (d.scoreSum) text += `\nTotal score: ${d.scoreSum.toFixed(2)}`;
        return text;
    });

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

    svg.call(d3.zoom()
        .scaleExtent([0.1, 10])
        .filter(() => !selectionManager.isSelectionMode())
        .on("zoom", ({transform}) => g.attr("transform", transform)));

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
        },
        toggleSelectionMode: () => {
            const mode = selectionManager.toggleSelectionMode();
            if (onModeChange) onModeChange(mode);
            return mode;
        }
    };
}

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
                newNodes.push({id: getNodeId(d), y: pos.y});
            }
        });

        newNodes.sort((a, b) => a.y - b.y);
        newNodes.forEach(({id}) => {
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

function processSelection(nodes, selected, order) {
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    return order.map(id => nodeMap.get(id)).filter(Boolean);
}

import * as d3 from 'd3';

export function createCanvas(div, nodes, links = null, onSelectionChange, onModeChange = null) {
    const container = d3.select(div);
    container.selectAll('*').remove();
    const containerNode = container.node();
    const rect = containerNode.getBoundingClientRect();

    let width = rect.width || 800;
    let height = rect.height || 600;
    const centerX = width / 2;
    const centerY = height / 2;

    const canvas = container.append("canvas")
        .attr("class", "network-canvas")
        .attr("width", width)
        .attr("height", height)
        .style("width", width + "px")
        .style("height", height + "px")
        .style("cursor", "default");

    const ctx = canvas.node().getContext("2d", { alpha: false });

    let transform = d3.zoomIdentity;
    const selectedNodes = new Set();
    const hoveredNode = { current: null };

    function handleResize() {
        const rect = containerNode.getBoundingClientRect();
        const newWidth = rect.width || 800;
        const newHeight = rect.height || 600;

        if (newWidth !== width || newHeight !== height) {
            width = newWidth;
            height = newHeight;

            canvas
                .attr("width", width)
                .attr("height", height)
                .style("width", width + "px")
                .style("height", height + "px");

            render();
        }
    }

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(containerNode);

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links)
            .id(d => d.id)
            .strength(d => d.strength)
            .distance(d => d.distance)
        )
        .force("charge", d3.forceManyBody().strength(-250))
        .force("center", d3.forceCenter(centerX, centerY).strength(0.7))
        .force("collide", d3.forceCollide(d => d.radius + 10).strength(0.5))
        .force("x", d3.forceX(centerX).strength(0.025))
        .force("y", d3.forceY(centerY).strength(0.025))
        .alphaDecay(0.05)
        .velocityDecay(0.6);

    let rafId = null;
    simulation.on("tick", () => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            render();
            rafId = null;
        });
    });

    simulation.tick(100);
    for (let i = 0; i < 100; i++) {
        simulation.tick();
    }
    simulation.alphaTarget(0);

    const selectionManager = createSelectionManager({
        canvas,
        nodes,
        transform: () => transform,
        hoveredNode,
        onSelectionChange: (selected, order) => {
            selectedNodes.clear();
            selected.forEach(id => selectedNodes.add(id));
            const selectedNodesArray = processSelection(nodes, selected, order);
            onSelectionChange(selectedNodesArray);
            render();
        },
        render: () => render() // Passer render comme callback
    });

    const zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .filter(event => !selectionManager.isSelectionMode() || event.type === 'wheel')
        .on("zoom", ({transform: t}) => {
            transform = t;
            render();
        });

    canvas.call(zoom);

    const {dragstarted, dragged, dragended} = createCanvasDragHandlers(
        canvas,
        nodes,
        simulation,
        () => transform,
        hoveredNode,
        () => !selectionManager.isSelectionMode(),
        render
    );

    selectionManager.setupInteractions(canvas, {
        start: dragstarted,
        drag: dragged,
        end: dragended
    });

    function render() {
        ctx.save();
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);

        ctx.translate(transform.x, transform.y);
        ctx.scale(transform.k, transform.k);

        ctx.strokeStyle = "#999";
        ctx.lineWidth = 1 / transform.k;

        links.forEach(link => {
            const sx = link.source.x;
            const sy = link.source.y;
            const tx = link.target.x;
            const ty = link.target.y;

            ctx.globalAlpha = Math.max(0.2, link.strength);
            ctx.lineWidth = link.width / transform.k;
            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(tx, ty);
            ctx.stroke();
        });

        ctx.globalAlpha = 1;
        nodes.forEach(node => {
            const isSelected = selectedNodes.has(node.id);
            // const isHovered = hoveredNode.current === node;

            ctx.fillStyle = node.color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
            ctx.fill();

            if (isSelected) {
                ctx.strokeStyle = "#0f2bff";
                ctx.lineWidth = 3 / transform.k;
                ctx.stroke();
            }
        });

        const rect = selectionManager.getSelectionRect();
        if (rect) {
            ctx.strokeStyle = "#0f2bff";
            ctx.fillStyle = "rgba(15, 43, 255, 0.2)";
            ctx.lineWidth = 2 / transform.k;

            const x = Math.min(rect.x1, rect.x2);
            const y = Math.min(rect.y1, rect.y2);
            const w = Math.abs(rect.x2 - rect.x1);
            const h = Math.abs(rect.y2 - rect.y1);

            ctx.fillRect(x, y, w, h);
            ctx.strokeRect(x, y, w, h);
        }

        ctx.restore();
    }

    render();

    return {
        destroy: () => {
            if (rafId) cancelAnimationFrame(rafId);
            simulation.stop();
            resizeObserver.disconnect();
            canvas.remove();
        },
        toggleSelectionMode: () => {
            const mode = selectionManager.toggleSelectionMode();
            if (onModeChange) onModeChange(mode);
            render();
            return mode;
        }
    };
}

function createSelectionManager(options) {
    const { canvas, nodes, transform, hoveredNode, onSelectionChange, render } = options;

    const selectedNodes = new Set();
    const selectionOrder = [];
    let selectionMode = false;
    let selectionRect = null;
    let selectionStart = null;

    function toggleSelectionMode() {
        selectionMode = !selectionMode;
        canvas.style("cursor", selectionMode ? "crosshair" : "default");
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

    function getNodeAtPosition(mx, my) {
        const t = transform();
        const x = (mx - t.x) / t.k;
        const y = (my - t.y) / t.k;

        for (let i = nodes.length - 1; i >= 0; i--) {
            const node = nodes[i];
            const dx = x - node.x;
            const dy = y - node.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < node.radius) {
                return node;
            }
        }
        return null;
    }

    function setupInteractions(canvasSelection, dragFunctions) {
        let draggedNode = null;

        canvasSelection.on("mousedown", function(event) {
            const [mx, my] = d3.pointer(event);
            const node = getNodeAtPosition(mx, my);

            if (selectionMode) {
                const t = transform();
                const x = (mx - t.x) / t.k;
                const y = (my - t.y) / t.k;
                selectionStart = { x, y, mx, my };
                selectionRect = { x1: x, y1: y, x2: x, y2: y };
                render();
            } else if (node) {
                draggedNode = node;
                dragFunctions.start(event, node);
            }
        });

        canvasSelection.on("mousemove", function(event) {
            const [mx, my] = d3.pointer(event);

            if (selectionMode) {
                if (selectionRect) {
                    const t = transform();
                    const x = (mx - t.x) / t.k;
                    const y = (my - t.y) / t.k;
                    selectionRect.x2 = x;
                    selectionRect.y2 = y;
                    render();
                }
            } else {
                if (draggedNode) {
                    dragFunctions.drag(event, draggedNode, mx, my);
                } else {
                    const node = getNodeAtPosition(mx, my);
                    if (hoveredNode.current !== node) {
                        hoveredNode.current = node;
                        canvasSelection.style("cursor", node ? "pointer" : "default");
                        render();
                    }
                }
            }
        });

        canvasSelection.on("mouseup", function(event) {
            if (selectionMode) {
                if (selectionRect) {
                    const x1 = Math.min(selectionRect.x1, selectionRect.x2);
                    const y1 = Math.min(selectionRect.y1, selectionRect.y2);
                    const x2 = Math.max(selectionRect.x1, selectionRect.x2);
                    const y2 = Math.max(selectionRect.y1, selectionRect.y2);

                    selectedNodes.clear();
                    selectionOrder.length = 0;

                    const newNodes = [];
                    nodes.forEach(d => {
                        if (d.x >= x1 && d.x <= x2 && d.y >= y1 && d.y <= y2) {
                            newNodes.push({ id: d.id, y: d.y });
                        }
                    });

                    newNodes.sort((a, b) => a.y - b.y);
                    newNodes.forEach(({ id }) => {
                        selectedNodes.add(id);
                        selectionOrder.push(id);
                    });

                    onSelectionChange(selectedNodes, selectionOrder);
                    selectionRect = null;
                    selectionStart = null;
                    render();
                }
            } else {
                if (draggedNode) {
                    dragFunctions.end(event, draggedNode);
                    draggedNode = null;
                } else {
                    const [mx, my] = d3.pointer(event);
                    const node = getNodeAtPosition(mx, my);
                    if (node) {
                        toggleNode(node.id);
                    }
                }
            }
        });
    }

    return {
        toggleSelectionMode,
        isSelectionMode: () => selectionMode,
        setupInteractions,
        getSelectionRect: () => selectionRect
    };
}

function createCanvasDragHandlers(canvas, nodes, simulation, getTransform, hoveredNode, isDraggable, render) {
    let dragSubject = null;

    function dragstarted(event, node) {
        if (!isDraggable()) return;
        if (!event.active) simulation.alphaTarget(0.3).restart();
        dragSubject = node;
        node.fx = node.x;
        node.fy = node.y;
    }

    function dragged(event, node, mx, my) {
        if (!dragSubject || !isDraggable()) return;
        const t = getTransform();
        node.fx = (mx - t.x) / t.k;
        node.fy = (my - t.y) / t.k;
        render();
    }

    function dragended(event, node) {
        if (!dragSubject || !isDraggable()) return;
        if (!event.active) simulation.alphaTarget(0);
        node.fx = null;
        node.fy = null;
        dragSubject = null;
    }

    return { dragstarted, dragged, dragended };
}

function processSelection(nodes, selected, order) {
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    return order.map(id => nodeMap.get(id)).filter(Boolean);
}

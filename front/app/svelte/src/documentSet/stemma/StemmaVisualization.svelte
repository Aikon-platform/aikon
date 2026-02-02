<script>
    import { onMount, onDestroy, createEventDispatcher } from 'svelte';
    import * as d3 from 'd3';

    export let documents = [];

    const dispatch = createEventDispatcher();

    let container;
    let canvas;
    let ctx;
    let width = 800;
    let height = 600;
    let transform = d3.zoomIdentity;
    let resizeObserver;
    let rafId = null;

    const NODE_WIDTH = 120;
    const NODE_HEIGHT = 40;

    let nodes = [];
    let edges = [];
    let draggedNode = null;
    let drawingEdge = null;
    let hoveredNode = null;
    let selectedNode = null;

    $: if (documents.length && container) initNodes(documents);

    function initNodes(docs) {
        const cols = Math.ceil(Math.sqrt(docs.length));
        const spacing = { x: NODE_WIDTH + 60, y: NODE_HEIGHT + 80 };

        nodes = docs.map((doc, i) => ({
            id: doc.id,
            title: doc.title || `Document ${doc.id}`,
            color: doc.color || '#999',
            x: (i % cols) * spacing.x + 100,
            y: Math.floor(i / cols) * spacing.y + 100,
            width: NODE_WIDTH,
            height: NODE_HEIGHT
        }));
        render();
    }

    function getNodeAt(mx, my) {
        const x = (mx - transform.x) / transform.k;
        const y = (my - transform.y) / transform.k;
        for (let i = nodes.length - 1; i >= 0; i--) {
            const n = nodes[i];
            if (x >= n.x && x <= n.x + n.width && y >= n.y && y <= n.y + n.height) {
                return n;
            }
        }
        return null;
    }

    function render() {
        if (!ctx) return;
        ctx.save();
        ctx.fillStyle = 'var(--bulma-scheme-main-bis, #999)';
        ctx.fillRect(0, 0, width, height);
        ctx.translate(transform.x, transform.y);
        ctx.scale(transform.k, transform.k);

        // Draw edges
        ctx.lineWidth = 2 / transform.k;
        edges.forEach(e => {
            const src = nodes.find(n => n.id === e.source);
            const tgt = nodes.find(n => n.id === e.target);
            if (src && tgt) drawArrow(src, tgt, '#999');
        });

        // Draw edge being created
        if (drawingEdge) {
            const src = nodes.find(n => n.id === drawingEdge.source);
            if (src) {
                ctx.strokeStyle = 'var(--bulma-link)';
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(src.x + src.width / 2, src.y + src.height);
                ctx.lineTo(drawingEdge.x, drawingEdge.y);
                ctx.stroke();
                ctx.setLineDash([]);
            }
        }

        // Draw nodes
        nodes.forEach(n => {
            const isHovered = hoveredNode === n;
            const isSelected = selectedNode === n;

            ctx.fillStyle = n.color;
            ctx.strokeStyle = isSelected ? 'var(--bulma-link)' : (isHovered ? '#333' : '#666');
            ctx.lineWidth = (isSelected ? 3 : (isHovered ? 2 : 1)) / transform.k;

            ctx.beginPath();
            ctx.roundRect(n.x, n.y, n.width, n.height, 4);
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = 'var(--bulma-scheme-main-bis, #f0f0f0)';
            ctx.font = `${12 / transform.k}px sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const label = n.title.length > 14 ? n.title.slice(0, 12) + '…' : n.title;
            ctx.fillText(label, n.x + n.width / 2, n.y + n.height / 2);
        });

        ctx.restore();
    }

    function drawArrow(src, tgt, color) {
        const sx = src.x + src.width / 2;
        const sy = src.y + src.height;
        const tx = tgt.x + tgt.width / 2;
        const ty = tgt.y;

        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(tx, ty);
        ctx.stroke();

        const angle = Math.atan2(ty - sy, tx - sx);
        const headLen = 10 / transform.k;
        ctx.beginPath();
        ctx.moveTo(tx, ty);
        ctx.lineTo(tx - headLen * Math.cos(angle - Math.PI / 6), ty - headLen * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(tx - headLen * Math.cos(angle + Math.PI / 6), ty - headLen * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
    }

    function handleMouseDown(e) {
        const [mx, my] = d3.pointer(e);
        const node = getNodeAt(mx, my);

        if (e.shiftKey && node) {
            drawingEdge = { source: node.id, x: (mx - transform.x) / transform.k, y: (my - transform.y) / transform.k };
        } else if (node) {
            draggedNode = node;
            selectedNode = node;
            dispatch('nodeselect', node);
        } else {
            selectedNode = null;
        }
        render();
    }

    function handleMouseMove(e) {
        const [mx, my] = d3.pointer(e);
        const worldX = (mx - transform.x) / transform.k;
        const worldY = (my - transform.y) / transform.k;

        if (drawingEdge) {
            drawingEdge.x = worldX;
            drawingEdge.y = worldY;
            render();
            return;
        }

        if (draggedNode) {
            draggedNode.x = worldX - draggedNode.width / 2;
            draggedNode.y = worldY - draggedNode.height / 2;
            render();
            return;
        }

        const node = getNodeAt(mx, my);
        if (node !== hoveredNode) {
            hoveredNode = node;
            canvas.style.cursor = node ? 'pointer' : 'default';
            render();
        }
    }

    function handleMouseUp(e) {
        if (drawingEdge) {
            const [mx, my] = d3.pointer(e);
            const target = getNodeAt(mx, my);
            if (target && target.id !== drawingEdge.source) {
                const exists = edges.some(ed => ed.source === drawingEdge.source && ed.target === target.id);
                if (!exists) {
                    edges = [...edges, { source: drawingEdge.source, target: target.id }];
                    dispatch('edgecreate', { source: drawingEdge.source, target: target.id });
                }
            }
            drawingEdge = null;
        }
        draggedNode = null;
        render();
    }

    function handleResize() {
        const rect = container.getBoundingClientRect();
        if (rect.width !== width || rect.height !== height) {
            width = rect.width || 800;
            height = rect.height || 600;
            canvas.width = width;
            canvas.height = height;
            render();
        }
    }

    onMount(() => {
        ctx = canvas.getContext('2d');
        handleResize();

        resizeObserver = new ResizeObserver(handleResize);
        resizeObserver.observe(container);

        const zoom = d3.zoom()
            .scaleExtent([0.2, 5])
            .filter(e => !e.shiftKey && (e.type === 'wheel' || (!draggedNode && !drawingEdge)))
            .on('zoom', ({ transform: t }) => {
                transform = t;
                render();
            });

        d3.select(canvas).call(zoom);
        if (documents.length) initNodes(documents);
    });

    onDestroy(() => {
        resizeObserver?.disconnect();
        if (rafId) cancelAnimationFrame(rafId);
    });

    export function removeEdge(source, target) {
        edges = edges.filter(e => !(e.source === source && e.target === target));
        render();
    }

    export function getGraph() {
        return { nodes: nodes.map(n => ({ id: n.id, x: n.x, y: n.y })), edges: [...edges] };
    }
</script>

<div class="stemma-container" bind:this={container}>
    <canvas
        bind:this={canvas}
        on:mousedown={handleMouseDown}
        on:mousemove={handleMouseMove}
        on:mouseup={handleMouseUp}
        on:mouseleave={() => { draggedNode = null; drawingEdge = null; }}
    ></canvas>
    <div class="stemma-hint">
        <span class="tag is-light is-small">Drag to move • Shift + drag to connect • Scroll to zoom</span>
    </div>
</div>

<style>
    .stemma-container {
        position: relative;
        width: 100%;
        height: 100%;
        min-height: 400px;
    }
    canvas {
        display: block;
        width: 100%;
        height: 100%;
    }
    .stemma-hint {
        position: absolute;
        bottom: 0.5rem;
        left: 0.5rem;
        pointer-events: none;
    }
</style>

<script>
    import { onMount, onDestroy, afterUpdate, createEventDispatcher } from 'svelte';
    import * as d3 from 'd3';
    import {i18n} from "../../utils.js";

    export let documents = [];
    export let stemmaStore;

    const { selectedNodes, edges, nodePositions, nodeTitles, updateNodeTitle, clearGraph } = stemmaStore;

    let container;
    let canvas;
    let ctx;
    let width = 800;
    let height = 600;
    let transform = d3.zoomIdentity;
    let resizeObserver;

    let bgColor, selectedColor, linkColor;

    const NODE_WIDTH = 120;
    const NODE_HEIGHT = 40;

    let nodes = [];
    let draggedNode = null;
    let drawingEdge = null;
    let hoveredNode = null;
    let editingNode = null;
    let editTitle = '';

    const t = {
        rename: {en: 'Rename node in stemma', fr: "Renommer un nœud au sein du stemma"},
        save: {en: 'Save', fr: "Enregistrer"},
        cancel: {en: 'Cancel', fr: "Annuler"},
        reset: { en: 'Reset stemma', fr: 'Réinitialiser le stemma' }
    }

    afterUpdate(render);

    function resetStemma() {
        clearGraph();
        initNodes(documents);
    }

    function extractCssColor(varName, fallback) {
        const temp = document.createElement('div');
        temp.style.color = `var(${varName}, ${fallback})`;
        document.body.appendChild(temp);
        const computed = getComputedStyle(temp).color;
        document.body.removeChild(temp);
        return computed;
    }

    function initNodes(docs) {
        const cols = Math.ceil(Math.sqrt(docs.length));
        const spacing = { x: NODE_WIDTH + 60, y: NODE_HEIGHT + 80 };

        nodes = docs.map((doc, i) => {
            const saved = $nodePositions[doc.id];
            const customTitle = $nodeTitles[doc.id];
            return {
                id: doc.id,
                title: customTitle || doc.title || `Document ${doc.id}`,
                color: doc.color || '#999',
                x: saved?.x ?? (i % cols) * spacing.x + 100,
                y: saved?.y ?? Math.floor(i / cols) * spacing.y + 100,
                width: NODE_WIDTH,
                height: NODE_HEIGHT
            };
        });
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
        ctx.fillStyle = bgColor;
        ctx.fillRect(0, 0, width, height);
        ctx.translate(transform.x, transform.y);
        ctx.scale(transform.k, transform.k);

        ctx.lineWidth = 2 / transform.k;
        $edges.forEach(e => {
            const src = nodes.find(n => n.id === e.source);
            const tgt = nodes.find(n => n.id === e.target);
            if (src && tgt) drawArrow(src, tgt, linkColor);
        });

        if (drawingEdge) {
            const src = nodes.find(n => n.id === drawingEdge.source);
            if (src) {
                ctx.strokeStyle = linkColor;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(src.x + src.width / 2, src.y + src.height);
                ctx.lineTo(drawingEdge.x, drawingEdge.y);
                ctx.stroke();
                ctx.setLineDash([]);
            }
        }

        const selectedIds = new Set($selectedNodes.map(n => n.id));
        nodes.forEach(n => {
            const isHovered = hoveredNode === n;
            const isSelected = selectedIds.has(n.id);

            ctx.fillStyle = n.color;
            ctx.strokeStyle = isSelected ? selectedColor : (isHovered ? selectedColor : n.color);
            ctx.lineWidth = (isSelected ? 3 : (isHovered ? 2 : 1)) / transform.k;

            ctx.beginPath();
            ctx.roundRect(n.x, n.y, n.width, n.height, 4);
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = '#222';
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

        if (node) {
             if (e.shiftKey || e.metaKey) {
                 drawingEdge = { source: node.id, x: (mx - transform.x) / transform.k, y: (my - transform.y) / transform.k };
             } else {
                 draggedNode = node;
             }
        }
        render();
    }

    function handleDblClick(e) {
        const [mx, my] = d3.pointer(e);
        const node = getNodeAt(mx, my);
        if (node) {
            editingNode = node;
            editTitle = node.title;
        }
    }

    function saveTitle() {
        if (editingNode && editTitle.trim()) {
            updateNodeTitle(editingNode.id, editTitle.trim());
            const node = nodes.find(n => n.id === editingNode.id);
            if (node) node.title = editTitle.trim();
            render();
        }
        editingNode = null;
    }

    function handleEditKeydown(e) {
        if (e.key === 'Enter') saveTitle();
        if (e.key === 'Escape') editingNode = null;
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
            const sourceId = drawingEdge.source;
            if (target && target.id !== sourceId) {
                const exists = $edges.some(ed => ed.source === sourceId && ed.target === target.id);
                if (!exists) {
                    const srcDoc = documents.find(d => d.id === sourceId);
                    const tgtDoc = documents.find(d => d.id === target.id);
                    stemmaStore.addEdge(sourceId, target.id, srcDoc, tgtDoc);
                }
            }
            drawingEdge = null;
        }

        if (draggedNode) {
            const {id, x, y} = draggedNode;
            stemmaStore.updateNodePosition(id, x, y);
            draggedNode = null;
        }
        render();
    }

    function handleResize() {
        if (!container || !canvas || !ctx) return;
        const rect = container.getBoundingClientRect();
        const newWidth = rect.width || 800;
        const newHeight = rect.height || 600;
        if (newWidth !== width || newHeight !== height) {
            width = newWidth;
            height = newHeight;
            canvas.width = width;
            canvas.height = height;
            render();
        }
    }

    onMount(() => {
        bgColor = extractCssColor('--bulma-scheme-main-bis', '#f9fafb');
        selectedColor = extractCssColor('--bulma-link', '#4258ff');
        linkColor = extractCssColor('--bulma-body-color', '#5a5f6b');

        ctx = canvas.getContext('2d');

        const rect = container.getBoundingClientRect();
        width = rect.width || 800;
        height = rect.height || 600;
        canvas.width = width;
        canvas.height = height;

        resizeObserver = new ResizeObserver(handleResize);
        resizeObserver.observe(container);

        const selection = d3.select(canvas);

        const zoom = d3.zoom()
            .scaleExtent([0.2, 5])
            .filter(e => !(e.shiftKey || e.metaKey) && (e.type === 'wheel' || (!draggedNode && !drawingEdge)))
            .on('zoom', ({ transform: t }) => {
                transform = t;
                render();
            });

        selection
            .call(zoom);

        if (documents.length) initNodes(documents);
    });

    onDestroy(() => {
        resizeObserver?.disconnect();
    });
</script>

<div class="stemma-container" bind:this={container}>
    <canvas
        bind:this={canvas}
        on:mousedown={handleMouseDown}
        on:mousemove={handleMouseMove}
        on:mouseup={handleMouseUp}
        on:dblclick={handleDblClick}
        on:mouseleave={() => { draggedNode = null; drawingEdge = null; }}
    />

    <button class="tag reset-btn" on:click={resetStemma} title={i18n('reset', t)}>
        <span class="icon is-small p-0">
            <i class="fas fa-undo"></i>
        </span>
    </button>
</div>

{#if editingNode}
    <div class="modal is-active">
        <div class="modal-background" on:click={() => editingNode = null} on:keydown={null}/>
        <div class="modal-content" style="max-width: 300px;">
            <div class="box">
                <h4 class="title is-6 mb-4">{i18n('rename', t)}</h4>
                <div class="field is-flex is-align-items-center" style="gap: 0.5rem;">
                    <span class="icon is-small is-left">
                        <span class="color-dot" style="background: {editingNode.color}"></span>
                    </span>
                    <div class="control">
                        <input class="input is-small"
                            type="text"
                            bind:value={editTitle}
                            on:keydown={handleEditKeydown}
                        />
                    </div>
                </div>
                <div class="buttons is-right">
                    <button class="button is-small" on:click={() => editingNode = null}>{i18n('cancel', t)}</button>
                    <button class="button is-small is-link" on:click={saveTitle}>{i18n('save', t)}</button>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .stemma-container {
        position: relative;
        width: 100%;
        min-height: 80vh;
        overflow: hidden;
    }
    canvas {
        display: block;
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: .5rem;
    }
    .color-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
    }
    .reset-btn {
        position: absolute;
        top: 0.5rem;
        left: 0.5rem;
        cursor: pointer;
    }
</style>

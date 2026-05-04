<script>
    import { onMount } from "svelte";
    import RightClick from "../../ui/RightClick.svelte";
    import StemmaNodeEditor from "./StemmaNodeEditor.svelte";
    import { i18n } from "../../utils.js";
    import { createStemmaInteraction } from "./stemmaInteraction.js";

    export let documents = [];
    export let stemmaStore;

    const {
        selectedNodes, edges, nodePositions, nodeTitles, reverseEdge,
        updateNodeTitle, updateEdgeLabel, addEdge, removeEdge, clearGraph
    } = stemmaStore;

    const interaction = createStemmaInteraction(stemmaStore);
    const { transform, dragOverride } = interaction;

    const NODE_W = 120;
    const NODE_H = 40;

    let svgEl;
    let width = 800, height = 600;
    let drawingEdge = null;
    let editingNode = null;
    let editingEdge = null;
    let editLabel = "";
    let menu = { open: false, x: 0, y: 0, items: [] };

    const t = {
        rename:      { en: "Rename", fr: "Renommer" },
        editEdge:    { en: "Qualify connection", fr: "Qualifier le lien" },
        deleteEdge:  { en: "Delete connection", fr: "Supprimer le lien" },
        reverseEdge: { en: "Reverse direction", fr: "Inverser la direction"},
        label:       { en: "Label (optional)", fr: "Libellé (optionnel)" },
        save:        { en: "Save", fr: "Enregistrer" },
        cancel:      { en: "Cancel", fr: "Annuler" },
        reset:       { en: "Reset stemma", fr: "Réinitialiser le stemma" },
    };

    $: nodes = documents.map((doc, i) => {
        const cols = Math.ceil(Math.sqrt(documents.length));
        const saved = $nodePositions[doc.id];
        return {
            id: doc.id,
            title: $nodeTitles[doc.id] || doc.title || `Document ${doc.id}`,
            color: doc.color || "#999",
            x: saved?.x ?? (i % cols) * (NODE_W + 60) + 100,
            y: saved?.y ?? Math.floor(i / cols) * (NODE_H + 80) + 100,
        };
    });

    $: nodeMap = new Map(nodes.map(n => [n.id, n]));
    $: visibleEdges = $edges
        .map(e => ({ ...e, source: nodeMap.get(e.source), target: nodeMap.get(e.target) }))
        .filter(e => e.source && e.target);

    onMount(() => {
        interaction.attach(svgEl, {
            onZoomFilter: e => !(e.shiftKey || e.metaKey) && (e.type === "wheel" || (!interaction.isDragging() && !drawingEdge))
        });
        if (nodes.length) interaction.positionCenter(nodes, { nodeWidth: NODE_W, nodeHeight: NODE_H });
    });

    function posOf(node, override) {
        return override?.docId === node.id ? { x: override.x, y: override.y } : { x: node.x, y: node.y };
    }

    function onNodePointerDown(e, node) {
        if (e.button !== 0) return;
        if (e.shiftKey || e.metaKey) {
            const { x, y } = interaction.toLocal?.(e) ?? localFromEvent(e);
            drawingEdge = { sourceId: node.id, x, y };
            svgEl.setPointerCapture(e.pointerId);
        } else if (interaction.startDrag(e, node)) {
            e.stopPropagation();
            svgEl.setPointerCapture(e.pointerId);
        }
    }

    function onPointerMove(e) {
        if (drawingEdge) {
            const { x, y } = localFromEvent(e);
            drawingEdge = { ...drawingEdge, x, y };
            return;
        }
        interaction.moveDrag(e);
    }

    function onPointerUp(e) {
        if (drawingEdge) {
            const target = nodeAtClient(e.clientX, e.clientY);
            if (target && target.id !== drawingEdge.sourceId) {
                const exists = $edges.some(ed => ed.source === drawingEdge.sourceId && ed.target === target.id);
                if (!exists) {
                    const src = documents.find(d => d.id === drawingEdge.sourceId);
                    const tgt = documents.find(d => d.id === target.id);
                    addEdge(drawingEdge.sourceId, target.id, src, tgt);
                }
            }
            drawingEdge = null;
        }
        interaction.endDrag();
        svgEl.releasePointerCapture?.(e.pointerId);
    }

    function localFromEvent(e) {
        const rect = svgEl.getBoundingClientRect();
        const tr = $transform;
        return { x: (e.clientX - rect.left - tr.x) / tr.k, y: (e.clientY - rect.top - tr.y) / tr.k };
    }

    function nodeAtClient(cx, cy) {
        const el = document.elementFromPoint(cx, cy);
        const g = el?.closest("[data-node-id]");
        return g ? nodeMap.get(Number(g.dataset.nodeId)) : null;
    }

    function onNodeContextMenu(e, node) {
        e.preventDefault();
        menu = {
            open: true, x: e.clientX, y: e.clientY,
            items: [
                { label: i18n("rename", t), icon: "pen", action: () => editingNode = { id: node.id, title: node.title, color: node.color } },
            ]
        };
    }

    function onEdgeContextMenu(e, edge) {
        e.preventDefault();
        menu = {
            open: true, x: e.clientX, y: e.clientY,
            items: [
                { label: i18n("editEdge", t), icon: "pen", action: () => { editingEdge = edge; editLabel = edge.label || ""; } },
                { label: i18n("reverseEdge", t), icon: "arrows-h", action: () => reverseEdge(edge.source.id, edge.target.id) },
                { label: i18n("deleteEdge", t), icon: "trash", danger: true, action: () => removeEdge(edge.source.id, edge.target.id) },
            ]
        };
    }

    function saveTitle({ detail }) {
        if (detail.title.trim()) updateNodeTitle(detail.id, detail.title.trim());
        editingNode = null;
    }

    function saveEdge() {
        if (editingEdge) updateEdgeLabel(editingEdge.source.id, editingEdge.target.id, editLabel.trim());
        editingEdge = null;
    }

    function onEdgeKeydown(e) {
        if (e.key === "Enter") saveEdge();
        if (e.key === "Escape") editingEdge = null;
    }

    $: selectedIds = new Set($selectedNodes.map(n => n.id));
</script>

<div class="stemma-container" bind:clientWidth={width} bind:clientHeight={height}>
    <svg bind:this={svgEl} class="stemma-svg"
         viewBox="0 0 {width} {height}"
         on:pointermove={onPointerMove} on:pointerup={onPointerUp}>
        <defs>
            <marker id="doc-arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="var(--bulma-body-color)"/>
            </marker>
        </defs>

        <g transform="translate({$transform.x},{$transform.y}) scale({$transform.k})">
            {#each visibleEdges as edge}
                {@const s = posOf(edge.source, $dragOverride)}
                {@const tg = posOf(edge.target, $dragOverride)}
                <g class="edge-group" on:contextmenu={e => onEdgeContextMenu(e, edge)}>
                    <line class="edge-hit"
                          x1={s.x + NODE_W/2} y1={s.y + NODE_H}
                          x2={tg.x + NODE_W/2} y2={tg.y}
                          stroke-width={10 / $transform.k}/>
                    <line class="edge"
                          x1={s.x + NODE_W/2} y1={s.y + NODE_H}
                          x2={tg.x + NODE_W/2} y2={tg.y}
                          stroke="var(--bulma-body-color)" stroke-width={2 / $transform.k}
                          marker-end="url(#doc-arrow)"/>
                </g>
                {#if edge.label}
                    <text x={(s.x + NODE_W/2 + tg.x + NODE_W/2) / 2}
                          y={(s.y + NODE_H + tg.y) / 2 - 4 / $transform.k}
                          font-size={10 / $transform.k}
                          text-anchor="middle"
                          fill="var(--bulma-body-color)">{edge.label}</text>
                {/if}
            {/each}

            {#if drawingEdge}
                {@const src = nodeMap.get(drawingEdge.sourceId)}
                {#if src}
                    <line x1={src.x + NODE_W/2} y1={src.y + NODE_H}
                          x2={drawingEdge.x} y2={drawingEdge.y}
                          stroke="var(--bulma-body-color)" stroke-width={2 / $transform.k}
                          stroke-dasharray="5,5"/>
                {/if}
            {/if}

            {#each nodes as node (node.id)}
                {@const p = posOf(node, $dragOverride)}
                {@const sel = selectedIds.has(node.id)}
                <g data-node-id={node.id}
                   transform="translate({p.x},{p.y})"
                   style="cursor: grab"
                   on:pointerdown={e => onNodePointerDown(e, node)}
                   on:contextmenu={e => onNodeContextMenu(e, node)}>
                    <rect width={NODE_W} height={NODE_H} rx="4"
                          fill={node.color}
                          stroke={sel ? "var(--bulma-link)" : node.color}
                          stroke-width={sel ? 3 / $transform.k : 1 / $transform.k}/>
                    <text x={NODE_W/2} y={NODE_H/2}
                          font-size={12 / $transform.k}
                          text-anchor="middle" dominant-baseline="middle"
                          style="pointer-events: none; user-select: none;">
                        {node.title.length > 14 ? node.title.slice(0, 12) + "…" : node.title}
                    </text>
                    <title>{node.title}</title>
                </g>
            {/each}
        </g>
    </svg>

    <button class="tag reset-btn" on:click={() => clearGraph()} title={i18n("reset", t)}>
        <span class="icon is-small p-0"><i class="fas fa-undo"></i></span>
    </button>
</div>

<RightClick bind:open={menu.open} x={menu.x} y={menu.y} items={menu.items}/>

<StemmaNodeEditor node={editingNode} on:save={saveTitle} on:close={() => editingNode = null}/>

{#if editingEdge}
    <div class="modal is-active">
        <div class="modal-background" on:click={() => editingEdge = null} on:keydown={null}/>
        <div class="modal-content" style="max-width: 300px;">
            <div class="box">
                <h4 class="title is-6 mb-4">{i18n("editEdge", t)}</h4>
                <div class="field is-flex is-align-items-center" style="gap: 0.5rem;">
                    <span class="color-dot" style="background: {editingEdge.source.color}"/>
                    <span>→</span>
                    <span class="color-dot" style="background: {editingEdge.target.color}"/>
                </div>
                <div class="control">
                    <input class="input is-small" type="text" bind:value={editLabel} on:keydown={onEdgeKeydown}/>
                </div>
                <div class="buttons is-right mt-3">
                    <button class="button is-small" on:click={() => editingEdge = null}>{i18n("cancel", t)}</button>
                    <button class="button is-small is-link" on:click={saveEdge}>{i18n("save", t)}</button>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .stemma-container {
        position: relative;
        width: 100%;
        height: 60vh;
    }
    .stemma-svg {
        width: 100%;
        height: 100%;
        position: absolute;
        inset: 0;
        background-color: var(--bulma-scheme-main-bis);
        border-radius: .5rem;
        overflow: hidden;
    }
    .edge {
        cursor: pointer;
    }
    .edge-group:hover .edge {
        stroke-width: 3;
    }
    .edge-hit {
        stroke: transparent;
        fill: none;
        cursor: pointer;
        pointer-events: stroke;
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

import * as d3 from "d3";
import { writable, get } from "svelte/store";
import {i18n} from "../../utils.js";


const menuLabels = {
    rename:      { en: "Rename", fr: "Renommer" },
    deleteNode:  { en: "Delete node", fr: "Supprimer le nœud" },
    editEdge:    { en: "Qualify connection", fr: "Qualifier le lien" },
    deleteEdge:  { en: "Delete connection", fr: "Supprimer le lien" },
    reverseEdge: { en: "Reverse direction", fr: "Inverser la direction" },
};

export function createStemmaInteraction(stemmaStore) {
    const { updateNodePosition } = stemmaStore;

    const transform = writable(d3.zoomIdentity);
    const dragOverride = writable(null);
    let drag = null;
    let zoomBehavior = null;
    let element = null;

    function attach(el, { onZoomFilter } = {}) {
        element = el;
        zoomBehavior = d3.zoom()
            .scaleExtent([0.2, 5])
            .filter(e => !drag && !get(drawingEdge) &&
                (onZoomFilter ? onZoomFilter(e) : (e.type === "wheel" || !(e.shiftKey || e.metaKey))))
            .on("zoom", e => transform.set(e.transform));
        d3.select(el).call(zoomBehavior);
    }

    function startDrag(e, node) {
        if (e.button !== 0) return false;
        const p = toLocal(e);
        drag = { node, startX: p.x, startY: p.y, originX: node.x, originY: node.y, moved: false };
        return true;
    }

    function moveDrag(e, threshold = 3) {
        if (!drag) return false;
        const p = toLocal(e);
        const dx = p.x - drag.startX, dy = p.y - drag.startY;
        if (!drag.moved && Math.hypot(dx, dy) < threshold) return false;
        drag.moved = true;
        dragOverride.set({ docId: drag.node.docId ?? drag.node.id, x: drag.originX + dx, y: drag.originY + dy });
        return true;
    }

    function endDrag() {
        if (!drag) return false;
        const moved = drag.moved;
        const ov = get(dragOverride);
        if (moved && ov) updateNodePosition(ov.docId, ov.x, ov.y);
        drag = null;
        dragOverride.set(null);
        return moved;
    }

    function toLocal(e) {
        const rect = element.getBoundingClientRect();
        const t = get(transform);
        return { x: (e.clientX - rect.left - t.x) / t.k, y: (e.clientY - rect.top - t.y) / t.k };
    }

    function positionCenter(nodes, { nodeWidth = 0, nodeHeight = 0, padding = 10 } = {}) {
        if (!nodes?.length || !zoomBehavior || !element) return;
        const xs = nodes.map(n => n.x);
        const ys = nodes.map(n => n.y);
        const minX = Math.min(...xs);
        const minY = Math.min(...ys);
        const maxX = Math.max(...xs) + nodeWidth;
        const maxY = Math.max(...ys) + nodeHeight;
        const w = maxX - minX, h = maxY - minY;
        const rect = element.getBoundingClientRect();
        const k = Math.min((rect.width  - 2 * padding) / w, (rect.height - 2 * padding) / h, 1);
        const tx = (rect.width  - w * k) / 2 - minX * k;
        const ty = (rect.height - h * k) / 2 - minY * k;
        d3.select(element).call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(k));
    }

    const drawingEdge = writable(null);

    function enableEdgeDraw({ getNodeId, documents }) {
        edgeDraw = { getNodeId, documents };
    }
    let edgeDraw = null;

    function onPointerDown(e, node) {
        if (e.button !== 0) return;
        if (edgeDraw && (e.shiftKey || e.metaKey)) {
            const { x, y } = toLocal(e);
            drawingEdge.set({ sourceId: edgeDraw.getNodeId(node), x, y });
            element.setPointerCapture(e.pointerId);
            e.stopPropagation();
        } else if (startDrag(e, node)) {
            e.stopPropagation();
            element.setPointerCapture(e.pointerId);
        }
    }

    function onPointerMove(e) {
        const cur = get(drawingEdge);
        if (cur) {
            const { x, y } = toLocal(e);
            drawingEdge.set({ ...cur, x, y });
            return;
        }
        moveDrag(e);
    }

    function onPointerUp(e) {
        const cur = get(drawingEdge);
        if (cur) {
            const targetId = nodeIdAtClient(e.clientX, e.clientY);
            if (targetId != null && targetId !== cur.sourceId) {
                const src = edgeDraw.documents.find(d => d.id === cur.sourceId);
                const tgt = edgeDraw.documents.find(d => d.id === targetId);
                if (src && tgt) stemmaStore.addEdge(cur.sourceId, targetId, src, tgt);
            }
            drawingEdge.set(null);
        }
        endDrag();
        element.releasePointerCapture?.(e.pointerId);
    }

    function nodeIdAtClient(cx, cy) {
        const el = document.elementFromPoint(cx, cy);
        const g = el?.closest("[data-node-id]");
        return g ? Number(g.dataset.nodeId) : null;
    }

    return {
        transform,
        dragOverride,
        drawingEdge,
        attach,
        enableEdgeDraw,
        onPointerDown,
        onPointerMove,
        onPointerUp,
        startDrag,
        moveDrag,
        endDrag,
        positionCenter,
        toLocal,
        isDragging: () => !!drag
    };
}

export function createStemmaMenu(stemmaStore, { onRename, onEditEdge }) {
    const { removeNode, removeEdge, reverseEdge } = stemmaStore;
    const menu = writable({ open: false, x: 0, y: 0, items: [] });

    const open = (e, items) => {
        e.preventDefault();
        menu.set({ open: true, x: e.clientX, y: e.clientY, items });
    };

    function openNodeMenu(e, node, extraActions = [], addDefaultActions = true) {
        open(e, [
            ...extraActions,
            ...(addDefaultActions ? [
                { label: i18n("rename", menuLabels), icon: "pen", action: () => onRename(node) },
                { label: i18n("deleteNode", menuLabels), icon: "trash", danger: true, action: () => removeNode(node.id ?? node.docId) },
            ] : []),
        ]);
    }

    function openEdgeMenu(e, edge) {
        open(e, [
            { label: i18n("editEdge", menuLabels), icon: "pen", action: () => onEditEdge(edge) },
            { label: i18n("reverseEdge", menuLabels), icon: "arrows-h", action: () => reverseEdge(edge.source.id ?? edge.source.docId, edge.target.id ?? edge.target.docId) },
            { label: i18n("deleteEdge", menuLabels), icon: "trash", danger: true, action: () => removeEdge(edge.source.id ?? edge.source.docId, edge.target.id ?? edge.target.docId) },
        ]);
    }

    return { menu, openNodeMenu, openEdgeMenu };
}

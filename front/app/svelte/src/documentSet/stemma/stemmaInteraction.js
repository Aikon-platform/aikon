import * as d3 from "d3";
import { writable, get } from "svelte/store";

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
            .filter(e => !drag && (onZoomFilter ? onZoomFilter(e) : e.button === 0))
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

    function anchorTopLeft(node, padding = 40) {
        if (!node || !zoomBehavior) return;
        d3.select(element).call(
            zoomBehavior.transform,
            d3.zoomIdentity.translate(padding - node.x, padding - node.y)
        );
    }

    return {
        transform,
        dragOverride,
        attach,
        startDrag,
        moveDrag,
        endDrag,
        anchorTopLeft,
        isDragging: () => !!drag
    };
}

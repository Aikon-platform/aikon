import { writable, derived, get } from 'svelte/store';

export function createStemmaStore(documentSetStore) {
    const { documentNodes, selectedRegions } = documentSetStore;

    const selectedNodes = writable([]);
    const edges = writable([]);

    const filteredDocuments = derived(
        [documentNodes, selectedRegions],
        ([$documentNodes, $selectedRegions]) =>
            Array.from($documentNodes?.values() || [])
                .filter(doc => $selectedRegions.has(doc.id))
    );

    const orderedSelection = derived(selectedNodes, $nodes =>
        $nodes.map((n, idx) => ({ ...n, order: idx + 1 }))
    );

    function removeFromSelection(id) {
        selectedNodes.update($nodes => $nodes.filter(n => n.id !== id));
    }

    function clearSelection() {
        selectedNodes.set([]);
    }

    function addEdge(source, target, sourceDoc, targetDoc) {
        edges.update($edges => {
            const exists = $edges.some(e => e.source === source && e.target === target);
            if (exists) return $edges;
            return [...$edges, {
                source,
                target,
                sourceTitle: sourceDoc?.title || source,
                targetTitle: targetDoc?.title || target,
                sourceColor: sourceDoc?.color,
                targetColor: targetDoc?.color
            }];
        });
    }

    function removeEdge(source, target) {
        edges.update($edges =>
            $edges.filter(e => !(e.source === source && e.target === target))
        );
    }

    function clearEdges() {
        edges.set([]);
    }

    function getGraph() {
        return {
            nodes: get(selectedNodes).map(n => ({ id: n.id, x: n.x, y: n.y })),
            edges: get(edges)
        };
    }

    return {
        selectedNodes,
        edges,
        filteredDocuments,
        orderedSelection,
        removeFromSelection,
        clearSelection,
        addEdge,
        removeEdge,
        clearEdges,
        getGraph
    };
}

import { writable, derived, get } from 'svelte/store';

export function createStemmaStore(documentSetStore) {
    const { documentNodes, selectedRegions, visiblePairs, filteredDocPairStats, filteredDocStats, imageCountMap, pairIndex } = documentSetStore;

    const edges = writable([]);

    const filteredDocuments = derived(
        [documentNodes, selectedRegions],
        ([$documentNodes, $selectedRegions]) =>
            Array.from($documentNodes?.values() || [])
                .filter(doc => $selectedRegions.has(doc.id))
    );

    const selectedNodes = derived(
        [edges, filteredDocuments],
        ([$edges, $docs]) => {
            if (!$edges.length) return [];

            const nodeIds = new Set();
            $edges.forEach(e => {
                nodeIds.add(e.source);
                nodeIds.add(e.target);
            });

            const children = new Map();
            const inDegree = new Map();
            nodeIds.forEach(id => {
                children.set(id, []);
                inDegree.set(id, 0);
            });
            $edges.forEach(e => {
                children.get(e.source).push(e.target);
                inDegree.set(e.target, inDegree.get(e.target) + 1);
            });

            const sorted = [];
            const queue = [...nodeIds].filter(id => inDegree.get(id) === 0).sort((a, b) => a - b);

            while (queue.length) {
                queue.sort((a, b) => a - b);
                const id = queue.shift();
                sorted.push(id);
                for (const child of children.get(id)) {
                    inDegree.set(child, inDegree.get(child) - 1);
                    if (inDegree.get(child) === 0) queue.push(child);
                }
            }

            const docMap = new Map($docs.map(d => [d.id, d]));
            return sorted.map(id => docMap.get(id)).filter(Boolean);
        }
    );

    // Derived stores for matrix visualization
    const selectedNodeIds = derived(selectedNodes, $nodes => new Set($nodes.map(n => n.id)));

    const matrixScoreData = derived(
        [filteredDocPairStats, selectedNodeIds],
        ([$stats, $ids]) => {
            if (!$ids.size) return new Map();
            const filtered = new Map();
            for (const [key, value] of $stats.scoreCount) {
                const [id1, id2] = key.split('-').map(Number);
                if ($ids.has(id1) && $ids.has(id2)) {
                    filtered.set(key, value);
                }
            }
            return filtered;
        }
    );

    const matrixDocStats = derived(
        [filteredDocStats, selectedNodeIds],
        ([$stats, $ids]) => {
            if (!$ids.size) return new Map();
            const filtered = new Map();
            for (const [id, value] of $stats.scoreCount) {
                if ($ids.has(id)) filtered.set(id, value);
            }
            return filtered;
        }
    );

    const matrixImageCount = derived(
        [imageCountMap, selectedNodeIds],
        ([$counts, $ids]) => {
            if (!$ids.size) return new Map();
            const filtered = new Map();
            for (const [id, count] of $counts) {
                if ($ids.has(id)) filtered.set(id, count);
            }
            return filtered;
        }
    );

    function getPairsForDocPair(doc1Id, doc2Id) {
        const $pairIndex = get(pairIndex);
        const key = doc1Id < doc2Id ? `${doc1Id}-${doc2Id}` : `${doc2Id}-${doc1Id}`;
        return $pairIndex.byDocPair.get(key) || [];
    }

    function addEdge(source, target, sourceDoc, targetDoc) {
        edges.update($edges => {
            const exists = $edges.some(e => e.source === source && e.target === target);
            if (exists) return $edges;
            return [...$edges, {
                source, target,
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
            nodes: get(selectedNodes).map(n => ({ id: n.id })),
            edges: get(edges)
        };
    }

    return {
        selectedNodes,
        edges,
        filteredDocuments,
        addEdge,
        removeEdge,
        clearEdges,
        getGraph,
        // Matrix visualization data
        matrixScoreData,
        matrixDocStats,
        matrixImageCount,
        getPairsForDocPair
    };
}

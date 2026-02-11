import { writable, derived, get } from 'svelte/store';

const emptyGraph = { edges: [], nodePositions: {}, nodeTitles: {} };

export function createStemmaStore(documentSetStore) {
    const { docSetId, documentNodes, selectedRegions, filteredDocPairStats, filteredDocStats, imageCountMap, pairIndex, visiblePairIds } = documentSetStore;

    const stemmaGraph = writable(JSON.parse(localStorage.getItem(`stemmaGraph-${docSetId}`)) || emptyGraph);
    stemmaGraph.subscribe(graph => localStorage.setItem(`stemmaGraph-${docSetId}`, JSON.stringify(graph)));

    const edges = derived(stemmaGraph, $g => $g.edges);
    const nodePositions = derived(stemmaGraph, $g => $g.nodePositions);
    const nodeTitles = derived(stemmaGraph, $g => $g.nodeTitles || {});

    function updateNodeTitle(nodeId, title) {
        stemmaGraph.update($g => ({
            ...$g,
            nodeTitles: { ...$g.nodeTitles, [nodeId]: title }
        }));
    }

    function updateEdgeLabel(source, target, label) {
        stemmaGraph.update($g => ({
            ...$g,
            edges: $g.edges.map(e =>
                e.source === source && e.target === target ? { ...e, label } : e
            )
        }));
    }

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

    const selectedNodeIds = derived(selectedNodes, $nodes => new Set($nodes.map(n => n.id)));

    const matrixScoreData = derived(
        [filteredDocPairStats, selectedNodeIds],
        ([$stats, $ids]) => {
            if (!$ids.size) return new Map();
            const filtered = new Map();
            for (const [key, value] of $stats.scoreCount) {
                const [id1, id2] = key.split('-').map(Number);
                if ($ids.has(id1) && $ids.has(id2)) filtered.set(key, value);
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

    function getFilteredPairsForDocPair(doc1Id, doc2Id) {
        const $pairIndex = get(pairIndex);
        const $visibleIds = get(visiblePairIds);
        const key = doc1Id < doc2Id ? `${doc1Id}-${doc2Id}` : `${doc2Id}-${doc1Id}`;
        const pairs = $pairIndex.byDocPair.get(key) || [];
        return $visibleIds.size > 0
            ? pairs.filter(p => $visibleIds.has(`${p.id_1}-${p.id_2}`))
            : pairs;
    }

    function addEdge(source, target, sourceDoc, targetDoc) {
        stemmaGraph.update($g => {
            if ($g.edges.some(e => e.source === source && e.target === target)) return $g;
            return {
                ...$g,
                edges: [...$g.edges, {
                    source, target,
                    sourceTitle: sourceDoc?.title || source,
                    targetTitle: targetDoc?.title || target,
                    sourceColor: sourceDoc?.color,
                    targetColor: targetDoc?.color
                }]
            };
        });
    }

    function removeEdge(source, target) {
        stemmaGraph.update($g => ({
            ...$g,
            edges: $g.edges.filter(e => !(e.source === source && e.target === target))
        }));
    }

    function clearEdges() {
        stemmaGraph.update($g => ({ ...$g, edges: [] }));
    }

    function clearGraph() {
        stemmaGraph.set(emptyGraph);
    }

    function updateNodePosition(nodeId, x, y) {
        stemmaGraph.update($g => ({
            ...$g,
            nodePositions: { ...$g.nodePositions, [nodeId]: { x, y } }
        }));
    }

    function getGraph() {
        const $g = get(stemmaGraph);
        return {
            nodes: get(selectedNodes).map(n => ({ id: n.id, ...($g.nodePositions[n.id] || {}) })),
            edges: $g.edges
        };
    }

    return {
        selectedNodes,
        edges,
        nodePositions,
        nodeTitles,
        updateNodeTitle,
        updateEdgeLabel,
        filteredDocuments,
        addEdge,
        removeEdge,
        clearEdges,
        clearGraph,
        updateNodePosition,
        getGraph,
        matrixScoreData,
        matrixDocStats,
        matrixImageCount,
        getFilteredPairsForDocPair
    };
}

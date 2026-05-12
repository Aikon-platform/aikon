import { writable, derived, get } from "svelte/store";

const emptyGraph = { edges: [], nodePositions: {}, nodeTitles: {} };

export function createStemmaStore(documentSetStore) {
    const {
        docSetId, documentNodes, selectedDocuments, filteredDocPairStats, filteredDocStats,
        imageCountMap, visiblePairs, buildFriezeMatches,
        getFilteredPairsForDocPair, buildMatchesForAnchor, buildClusterMatches
    } = documentSetStore;

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
        [documentNodes, selectedDocuments],
        ([$documentNodes, $selectedDocuments]) =>
            Array.from($documentNodes?.values() || [])
                .filter(doc => $selectedDocuments.has(doc.id))
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

    const selectedViz = writable("");
    const selectedCell = writable(null);
    const selectedFriezeImage = writable(null);
    const selectedCluster = writable(null);

    selectedViz.subscribe(() => {
        selectedCell.set(null);
        selectedFriezeImage.set(null);
        selectedCluster.set(null);
    });

    const matches = derived(
        [selectedViz, selectedCell, selectedFriezeImage, selectedCluster, visiblePairs],
        ([$viz, $cell, $frieze, $cluster, $pairs]) => {
            if ($viz === "docMatrix" && $cell) return buildMatrixMatches($cell);
            if ($viz === "spatialFrieze" && $cluster) return buildClusterMatches($cluster);
            if ($viz === "spatialFrieze" && $frieze) return buildFriezeMatches($frieze, $pairs);
            return { matches: [], columns: [] };
        }
    );

    function buildMatrixMatches(cell) {
        return buildMatchesForAnchor(cell.doc1, [cell.doc2], null, false, true);
    }

    const matrixScoreData = derived(
        [filteredDocPairStats, selectedNodeIds],
        ([$stats, $ids]) => {
            if (!$ids.size) return new Map();
            const filtered = new Map();
            for (const [key, value] of $stats.scoreCount) {
                const [id1, id2] = key.split("-").map(Number);
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

    function addEdge(source, target, sourceDoc, targetDoc) {
        stemmaGraph.update($g => {
            if ($g.edges.some(e => e.source === source && e.target === target)) return $g;
            if ($g.edges.some(e => e.target === source && e.source === target)) return $g;
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

    function removeNode(id) {
        stemmaGraph.update($g => {
            const { [id]: _p, ...nodePositions } = $g.nodePositions;
            const { [id]: _t, ...nodeTitles } = $g.nodeTitles || {};
            return {
                ...$g,
                edges: $g.edges.filter(e => e.source !== id && e.target !== id),
                nodePositions,
                nodeTitles,
            };
        });
    }

    function reverseEdge(source, target) {
        stemmaGraph.update($g => {
            const idx = $g.edges.findIndex(e => e.source === source && e.target === target);
            if (idx < 0) return $g;
            const e = $g.edges[idx];
            const reversed = {
                ...e,
                source: e.target,
                target: e.source,
                sourceTitle: e.targetTitle,
                targetTitle: e.sourceTitle,
                sourceColor: e.targetColor,
                targetColor: e.sourceColor,
            };
            const edges = [...$g.edges];
            edges[idx] = reversed;
            return { ...$g, edges };
        });
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
        selectedViz,
        selectedCell,
        selectedCluster,
        selectedFriezeImage,
        matches,
        updateNodeTitle,
        updateEdgeLabel,
        filteredDocuments,
        addEdge,
        removeEdge,
        removeNode,
        reverseEdge,
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

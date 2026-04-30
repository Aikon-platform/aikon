import { writable, derived, get } from "svelte/store";

const emptyGraph = { edges: [], nodePositions: {}, nodeTitles: {} };

export function createStemmaStore(documentSetStore) {
    const {
        docSetId, documentNodes, selectedDocuments, filteredDocPairStats, filteredDocStats,
        imageCountMap, pairIndex, visiblePairIds, visiblePairs, imageNodes
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

    selectedViz.subscribe(() => {
        selectedCell.set(null);
        selectedFriezeImage.set(null);
    });

    const matches = derived(
        [selectedViz, selectedCell, selectedFriezeImage, imageNodes, documentNodes, visiblePairs],
        ([$viz, $cell, $frieze, $imgNodes, $docNodes, $pairs]) => {
            if ($viz === "docMatrix" && $cell) return buildMatrixMatches($cell, $imgNodes, $docNodes);
            if ($viz === "spatialFrieze" && $frieze) return buildFriezeMatches($frieze, $imgNodes, $docNodes, $pairs);
            return { matches: [], columns: [] };
        }
    );

    function otherSide(pair, anchorDocId, anchorImgId, imgNodes, docNodes) {
        const isFrom1 = pair.digit_1 === anchorDocId && (anchorImgId == null || pair.id_1 === anchorImgId);
        const isFrom2 = pair.digit_2 === anchorDocId && (anchorImgId == null || pair.id_2 === anchorImgId);
        if (!isFrom1 && !isFrom2) return null;
        const targetId = isFrom1 ? pair.id_2 : pair.id_1;
        const targetDocId = isFrom1 ? pair.digit_2 : pair.digit_1;
        const image = imgNodes.get(targetId);
        const doc = docNodes.get(targetDocId);
        return image && doc ? { image, doc, score: pair.weightedScore } : null;
    }

    function buildMatchesForAnchor(anchorDoc, targetDocs, imgNodes, docNodes) {
        const byAnchor = new Map();

        for (const targetDoc of targetDocs) {
            if (targetDoc.id === anchorDoc.id) continue;
            const pairs = getFilteredPairsForDocPair(anchorDoc.id, targetDoc.id);
            for (const p of pairs) {
                const anchorOnSide1 = p.digit_1 === anchorDoc.id;
                const anchorId = anchorOnSide1 ? p.id_1 : p.id_2;
                const target = otherSide(p, anchorDoc.id, anchorId, imgNodes, docNodes);
                const anchorImg = imgNodes.get(anchorId);
                if (!anchorImg || !target) continue;

                if (!byAnchor.has(anchorId)) {
                    byAnchor.set(anchorId, { anchor: anchorImg, byTargetDoc: new Map() });
                }
                const entry = byAnchor.get(anchorId);
                if (!entry.byTargetDoc.has(targetDoc.id)) entry.byTargetDoc.set(targetDoc.id, []);
                entry.byTargetDoc.get(targetDoc.id).push(target.image);
            }
        }

        const rows = Array.from(byAnchor.values())
            .sort((a, b) => (a.anchor.canvas ?? Infinity) - (b.anchor.canvas ?? Infinity))
            .map(({ anchor, byTargetDoc }) => [
                { images: [anchor], doc: anchorDoc },
                ...targetDocs.map(td => {
                    const imgs = byTargetDoc.get(td.id);
                    return imgs?.length ? { images: imgs, doc: td } : null;
                }),
            ]);

        const columns = [{ doc: anchorDoc }, ...targetDocs.map(d => ({ doc: d }))];
        return assignIndices({ matches: rows, columns });
    }

    function buildMatrixMatches(cell, imgNodes, docNodes) {
        return buildMatchesForAnchor(cell.doc1, [cell.doc2], imgNodes, docNodes);
    }

    function buildFriezeMatches(frieze, imgNodes, docNodes, pairs) {
        const baseDoc = docNodes.get(frieze.baseDocId);
        const sourceImage = imgNodes.get(frieze.imageId);
        if (!baseDoc || !sourceImage) return { matches: [], columns: [] };

        const bestPerDoc = new Map();
        for (const p of pairs) {
            const target = otherSide(p, frieze.baseDocId, frieze.imageId, imgNodes, docNodes);
            if (!target || target.doc.id === frieze.baseDocId) continue;
            const existing = bestPerDoc.get(target.doc.id);
            if (!existing || target.score > existing.score) bestPerDoc.set(target.doc.id, target);
        }

        const targets = Array.from(bestPerDoc.values());
        const row = [
            { images: [sourceImage], doc: baseDoc },
            ...targets.map(t => ({ images: [t.image], doc: t.doc })),
        ];
        const columns = [{ doc: baseDoc }, ...targets.map(t => ({ doc: t.doc }))];
        return assignIndices({ matches: [row], columns });
    }

    function assignIndices(data) {
        let idx = 0;
        for (const row of data.matches) {
            for (const cell of row) {
                if (!cell) continue;
                cell.indices = cell.images.map(() => idx++);
            }
        }
        return data;
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
        selectedViz,
        selectedCell,
        selectedFriezeImage,
        matches,
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

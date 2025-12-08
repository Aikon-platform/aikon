import {derived, writable, get} from 'svelte/store';
import {initPagination, pageUpdate} from "../utils.js";

export function createClusterStore(documentSetStore) {
    const pageLength = 10;
    const currentPage = writable(1);

    const { allPairs, imageNodes } = documentSetStore;

    initPagination(currentPage, "p");

    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "p");
    }

    const validatedClusters = writable(new Set());

    function findClusters(imgPairs, imageIds) {
        const parent = new Map();

        const find = (img) => {
            if (!parent.has(img)) {
                parent.set(img, img);
                return img;
            }
            if (parent.get(img) !== img) {
                parent.set(img, find(parent.get(img)));
            }
            return parent.get(img);
        };

        const union = (a, b) => {
            const rootA = find(a);
            const rootB = find(b);
            if (rootA !== rootB) {
                parent.set(rootB, rootA);
            }
        };

        imgPairs.forEach(p => union(p.id_1, p.id_2));

        const clusterMap = new Map();
        imageIds.forEach(imgId => {
            const root = find(imgId);
            if (!clusterMap.has(root)) {
                clusterMap.set(root, []);
            }
            clusterMap.get(root).push(imgId);
        });

        return Array.from(clusterMap.values())
            .map(members => {
                const n = members.length;
                const maxEdges = (n * (n - 1)) / 2;
                const imageSet = new Set(members);
                const actualLinks = imgPairs.filter(p =>
                    imageSet.has(p.id_1) && imageSet.has(p.id_2)
                ).length;

                return {
                    id: crypto.randomUUID(),
                    members,
                    size: n,
                    fullyConnected: actualLinks === maxEdges
                };
            })
            .sort((a, b) => b.size - a.size);
    }

    /**
     * Clusters { id, members: [imgId1, imgId2, ...], size, fullyConnected }
     */
    const imageClusters = derived(allPairs, ($pairs) => {
        if (!$pairs.length) return [];
        return findClusters($pairs, Array.from(get(imageNodes).keys()));
    });

    const paginatedClusters = derived([imageClusters, validatedClusters, currentPage], ([$clusters, $validated, $currentPage]) => {
        const start = ($currentPage - 1) * pageLength;
        const end = start + pageLength;
        return $clusters
            .slice(start, end)
            .map(cluster => ({
                ...cluster,
                fullyConnected: cluster.fullyConnected || $validated.has(cluster.id)
            }));
    });

    function clusterValidation(clusterId) {
        validatedClusters.update(set => new Set(set).add(clusterId));
    }

    return {
        paginatedClusters,
        imageClusters,
        clusterNb: derived(imageClusters, $clusters => $clusters.length),
        clusterValidation,
        handlePageUpdate,
        pageLength,
        currentPage
    };
}

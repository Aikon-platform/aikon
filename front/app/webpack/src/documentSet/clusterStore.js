import {derived, writable, get} from 'svelte/store';
import {initPagination, pageUpdate, withLoading} from "../utils.js";
import {appName, csrfToken} from "../constants.js";

export function createClusterStore(documentSetStore, clusterSelection) {
    const pageLength = 10;
    const currentPage = writable(1);

    const {allPairs, imageNodes} = documentSetStore;

    initPagination(currentPage, "p");

    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "p");
    }

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

    // UI clusters, manipulable without needing to rerun findClusters
    const interfaceClusters = writable([]);
    imageClusters.subscribe($clusters => {
        interfaceClusters.set($clusters);
    });

    const paginatedClusters = derived([interfaceClusters, currentPage], ([$clusters, $currentPage]) => {
        const start = ($currentPage - 1) * pageLength;
        const end = start + pageLength;
        return $clusters.slice(start, end);
    });

    const imgRef2pairData = (imgRef) => {
        const [regionId, ...rest] = imgRef.split('_');
        return {img: rest.join('_'), regionId};
    };

    const pairData = (ref1, ref2) => {
        const {img: img1, regionId: reg1} = imgRef2pairData(ref1);
        const {img: img2, regionId: reg2} = imgRef2pairData(ref2);
        return {
            img_1: img1, img_2: img2,
            regions_id_1: reg1, regions_id_2: reg2
        };
    };

    const removeImgRefs = async (imgRefs) => {
        const imgRefArray = Array.isArray(imgRefs) ? imgRefs : Object.keys(imgRefs);
        const imgRefSet = new Set(imgRefArray);

        const byOriginCluster = {};
        get(interfaceClusters).forEach(cluster => {
            const selected = cluster.members.filter(m => imgRefSet.has(m));
            if (selected.length > 0) {
                byOriginCluster[cluster.id] = selected;
            }
        });

        const pairsToRemove = Object.entries(byOriginCluster).flatMap(([clusterId, selectedRefs]) => {
            const cluster = get(interfaceClusters).find(c => c.id === clusterId);
            if (!cluster) return [];

            const remaining = cluster.members.filter(m => !imgRefSet.has(m));
            return selectedRefs.flatMap(sel =>
                remaining.map(rem => pairData(sel, rem))
            );
        });

        if (pairsToRemove.length === 0) return true;

        try {
            await withLoading(() => fetch(`${window.location.origin}/${appName}/uncategorize-pair-batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({pairs: pairsToRemove})
            }));

            interfaceClusters.update($clusters =>
                $clusters
                    .map(c => {
                        if (!byOriginCluster[c.id]) return c;

                        const remaining = c.members.filter(m => !imgRefSet.has(m));
                        return {...c, members: remaining, size: remaining.length};
                    })
                    .filter(c => c.size > 0)
            );

            return true;
        } catch (error) {
            console.error('Error:', error);
            return false;
        }
    };

    const makePairsExactMatch = async (imgRefs) => {
        const pairs = imgRefs.flatMap((ref1, i) =>
            imgRefs.slice(i + 1).map(ref2 => pairData(ref1, ref2))
        );

        try {
            const response = await withLoading(() => fetch(`${window.location.origin}/${appName}/exact-match-batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({pairs})
            }));

            if (!response.ok) {
                console.error('Batch validation failed');
                return false;
            }

            return true;
        } catch (error) {
            console.error('Error:', error);
            return false;
        }
    };

    const validateCluster = async (cluster) => {
        const success = await makePairsExactMatch(cluster.members);

        if (success) {
            interfaceClusters.update($clusters =>
                $clusters.map(c =>
                    c.id === cluster.id ? {...c, fullyConnected: true} : c
                )
            );
        }

        return success;
    };

    const createCluster = async (imgRefs) => {
        if (imgRefs.length < 2) {
            window.alert('Need at least 2 images');
            return false;
        }

        const success = await makePairsExactMatch(imgRefs);

        if (success) {
            interfaceClusters.update($clusters => {
                const newCluster = {
                    id: crypto.randomUUID(),
                    members: imgRefs,
                    size: imgRefs.length,
                    fullyConnected: true
                };

                return [newCluster, ...$clusters].sort((a, b) => b.size - a.size);
            });
        }

        return success;
    };

    const selectedRegions = () => Object.values(get(clusterSelection).selected)[0] || {};

    const newCluster = async () => {
        const selected = selectedRegions();
        const imgRefs = Object.keys(selected);

        if (imgRefs.length < 2) {
            window.alert('Need at least 2 images');
            return false;
        }

        const removed = await removeImgRefs(imgRefs);
        if (!removed) return false;

        const created = await createCluster(imgRefs);
        if (!created) return false;

        clusterSelection.empty();
        return true;
    };

    const removeFromClusters = async () => {
        const selected = selectedRegions();
        const removed = await removeImgRefs(Object.keys(selected));
        if (!removed) return false;
        clusterSelection.empty();
        return true;
    };

    return {
        imageClusters,
        interfaceClusters,
        clusterNb: derived(interfaceClusters, $clusters => $clusters.length),

        validateCluster,
        removeFromClusters,
        newCluster,

        paginatedClusters,
        handlePageUpdate,
        pageLength,
        currentPage
    };
}

import {derived, writable, get} from 'svelte/store';
import {initPagination, pageUpdate, showMessage, withLoading} from "../utils.js";
import {appLang, appName, csrfToken} from "../constants.js";

export function createClusterStore(documentSetStore, clusterSelection) {
    const pageLength = 10;
    const currentPage = writable(1);

    const {allPairs, imageNodes} = documentSetStore;

    initPagination(currentPage, "p");

    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "p");
    }

    function findClusters(pairs) {
        if (pairs.length === 0) return [];
        const parent = new Map();
        const ref2Id = new Map();

        const find = (ref) => {
            if (!parent.has(ref)) {
                parent.set(ref, ref);
                return ref;
            }
            if (parent.get(ref) !== ref) {
                parent.set(ref, find(parent.get(ref)));
            }
            return parent.get(ref);
        };

        const union = (a, b) => {
            const rootA = find(a);
            const rootB = find(b);
            if (rootA !== rootB) {
                parent.set(rootB, rootA);
            }
        };

        const refs = new Set();
        pairs.forEach(p => {
            if (p.category === 1) {
                union(p.ref_1, p.ref_2);
                refs.add(p.ref_1);
                refs.add(p.ref_2);

                ref2Id.set(p.ref_1, p.id_1);
                ref2Id.set(p.ref_2, p.id_2);
            }
        });

        const clusterMap = new Map();
        refs.forEach(ref => {
            const root = find(ref);
            if (!clusterMap.has(root)) {
                clusterMap.set(root, []);
            }
            clusterMap.get(root).push(ref2Id.get(ref));
        });

        return Array.from(clusterMap.values())
            .map(members => {
                const n = members.length;
                const maxEdges = (n * (n - 1)) / 2;
                const imageSet = new Set(members);
                const actualLinks = pairs.filter(p =>
                    p.category === 1 &&
                    imageSet.has(p.id_1) && imageSet.has(p.id_2)
                ).length;

                return {
                    id: crypto.randomUUID(),
                    members,
                    size: n,
                    fullyConnected: actualLinks === maxEdges
                };
            })
            .filter(c => c.size > 1)
            .sort((a, b) => b.size - a.size);
    }

    /**
     * Clusters { id, members: [imgId1, imgId2, ...], size, fullyConnected }
     */
    const imageClusters = derived(allPairs, ($pairs) => {
        if (!$pairs.length) return [];
        return findClusters($pairs);
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
            // regions_id_1: reg1, regions_id_2: reg2
        };
    };

    const removeImgsFromInterface = (imgRefSet, byOriginCluster) => {
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
    }

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

        if (pairsToRemove.length === 0) {
            removeImgsFromInterface(imgRefSet, byOriginCluster)
            return true;
        }

        try {
            const response = await withLoading(() => fetch(`${window.location.origin}/${appName}/uncategorize-pair-batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({pairs: pairsToRemove})
            }));

            if (!response.ok) {
                console.log(response)
                await showMessage(
                    appLang === "en" ? "Batch un-categorization failed" : "La dé-catégorisation par lot a échoué",
                    appLang === "en" ? "Error" : "Erreur",
                );
                return false;
            }

            removeImgsFromInterface(imgRefSet, byOriginCluster);

            return true;
        } catch (error) {
            await showMessage(
                error,
                appLang === "en" ? "Error" : "Erreur",
            );
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
                console.log(response)
                await showMessage(
                    appLang === "en" ? "Batch validation failed" : "La validation par lot a échoué",
                    appLang === "en" ? "Error" : "Erreur",
                );
                return false;
            }

            return true;
        } catch (error) {
            await showMessage(
                error,
                appLang === "en" ? "Error" : "Erreur",
            );
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
        const confirmed = await showMessage(
            appLang === "en" ? "Do you want to create a cluster out of these images?" : "Voulez-vous créer un cluster à partir de ces images ?",
            appLang === "en" ? "Confirm creation" : "Confirmer la création",
            true
        );
        if (!confirmed) {
            return; // User cancelled the creation
        }

        const selected = selectedRegions();
        const imgRefs = Object.keys(selected);

        if (imgRefs.length < 2) {
            await showMessage(
                appLang === "en" ? "Cluster creation requires at least 2 images" : "La création d'un nouveau cluster nécessite a minima 2 images",
                appLang === "en" ? "Impossible creation" : "Création impossible",
            );
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
        const confirmed = await showMessage(
            appLang === "en" ? "Do you want to remove these images from their clusters?" : "Voulez-vous supprimer ces images de leurs clusters ?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );
        if (!confirmed) {
            return; // User cancelled the deletion
        }

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

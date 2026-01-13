<script>
    import { onMount, onDestroy } from 'svelte';
    import { createSvg } from "./network-svg.js";

    export let cluster;
    export let pairIndex;

    let container;
    let networkInstance;

    onMount(() => {
        if (container && cluster.members.length > 0) {
            const members = new Set(cluster.members);
            const links = [];
            const processed = new Set();
            members.forEach(imgId => {
                const pairs = pairIndex.get(imgId) || [];
                pairs.forEach(pair => {
                    const other = pair.id_1 === imgId ? pair.id_2 : pair.id_1;
                    if (members.has(other)) {
                        const key = [imgId, other].sort().join('-');
                        if (!processed.has(key)) {
                            processed.add(key);
                            links.push({ source: imgId, target: other });
                        }
                    }
                });
            });
            networkInstance = createSvg(container, cluster.members.map(id => ({ id })), links);
        }
    });

    onDestroy(() => {
        networkInstance?.destroy();
    });
</script>

<div bind:this={container} class="cluster-network"></div>

<style>
    .cluster-network {
        display: inline-block;
    }
</style>

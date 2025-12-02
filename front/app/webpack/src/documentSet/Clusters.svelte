<script>
    import Region from "../regions/Region.svelte";
    import Table from "../Table.svelte";
    import Row from "../Row.svelte";
    export let documentSetStore;
    const {
        imageClusters,
        imageNodes,
    } = documentSetStore;

    $: onlyPartial = true;
    $: onlyNotValidated = true;
</script>

<Table>
    {#each $imageClusters as cl (cl.id)}
        <Row>
            <svelte:fragment slot="row-header">
                <div class="cluster-info">
                    <span class="cluster-size">{cl.size} images</span>
                    {#if !cl.fullyConnected}
                        <button class="button is-small is-warning">Validate</button>
                    {/if}
                </div>
            </svelte:fragment>
            <svelte:fragment slot="row-body">
                {#each cl.members as imgId}
                    <Region item={$imageNodes.get(imgId)} copyable={false}/>
                {/each}
            </svelte:fragment>
        </Row>
    {/each}
</Table>

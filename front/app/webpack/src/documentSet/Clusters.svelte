<script>
    import Region from "../regions/Region.svelte";
    import Table from "../Table.svelte";
    import Row from "../Row.svelte";

    export let documentSetStore;
    const {
        imageClusters,
        imageNodes
    } = documentSetStore;

    $: onlyPartial = true;
    $: onlyNotValidated = true;
    console.log($imageClusters);
</script>

<Table>
    {#each $imageClusters as cl (cl.id)}
        <Row>
            <svelte:fragment slot="row-header">
                <!-- small network representation + if not fully connected, add validate button -->
            </svelte:fragment>
            <svelte:fragment slot="row-body">
                {#each cl.members as imgId}
                    <Region item={$imageNodes.get(imgId)} copyable={false}/>
                {/each}
            </svelte:fragment>
        </Row>
    {/each}
</Table>

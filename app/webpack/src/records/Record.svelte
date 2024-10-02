<script>
    import SelectBtn from "./SelectBtn.svelte";
    import Item from "./Item.svelte";
    export let item;
    export let recordsStore;
</script>

<Item {item} {recordsStore}>
    <div slot="buttons">
        <SelectBtn {item}/>
    </div>

    <div slot="body" class="grid metadata pt-2">
        {#each Object.entries(item.metadata) as [field, value]}
            <div class="datum is-middle columns">
                <div class="column is-4 is-bold">{field}</div>
                <div class="column is-8 {value === '-' ? 'faded' : ''}">{@html value}</div>
            </div>
        {/each}
    </div>
</Item>

<style>
    .metadata {
        color: var(--bulma-text-strong);
    }
    .metadata .datum:not(:nth-last-child(-n+2)) {
        border-bottom: 1px solid var(--bulma-border);
    }
    .columns {
        margin-bottom: 0.5rem;
    }
</style>

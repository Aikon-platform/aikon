<script>
    export let items = [];     // [{ label, icon?, disabled?, danger?, action }]
    export let x = 0;
    export let y = 0;
    export let open = false;

    function close() { open = false; }
    function pick(item) {
        if (item.disabled) return;
        item.action?.();
        close();
    }
</script>

<svelte:window on:click={close} on:contextmenu|capture={e => { if (open && !e.target.closest('.ctx-menu')) close(); }} on:keydown={e => e.key === 'Escape' && close()}/>

{#if open && items.length}
    <ul class="ctx-menu box p-1" style="left:{x}px;top:{y}px">
        {#each items as item}
            {#if item.separator}
                <li><hr class="dropdown-divider"/></li>
            {:else}
                <li>
                    <button class="button is-small is-ghost has-text-left has-text-dark has-text-weight-normal"
                            class:has-text-danger={item.danger}
                            disabled={item.disabled}
                            on:click={() => pick(item)}>
                        {#if item.icon}
                            <span class="icon is-small">
                                <i class="fas fa-{item.icon}"/>
                            </span>
                        {/if}
                        <span>{item.label}</span>
                    </button>
                </li>
            {/if}
        {/each}
    </ul>
{/if}

<style>
    .ctx-menu {
        position: fixed;
        z-index: 1000;
        min-width: 180px;
        list-style: none;
        border-radius: .1em;
    }
</style>

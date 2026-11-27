<script>
    /**
     * @typedef {Object} Props
     * @property {{ id: string, label: string }[]} [tabs]
     * @property {any} [activeTab]
     * @property {import('svelte').Snippet<[any]>} [children]
     */

    /** @type {Props} */
    let { tabs = [], activeTab = $bindable(tabs[0]?.id ?? ""), children } = $props();
</script>

{#if tabs.length > 1}
    <nav class="tabs-bar pb-2">
        <div class="tabs">
            <ul>
                {#each tabs as {id, label}}
                    <li class:is-active={activeTab === id}>
                        <a href={null} onclick={(e) => { preventDefault(); activeTab = id }}>{label}</a>
                    </li>
                {/each}
            </ul>
        </div>
    </nav>
{/if}

<div class="tab-content">
    {@render children?.({ activeTab, })}
</div>

<style>
    .tab-content {
        flex: 1;
        overflow: auto;
        padding: 1rem;
    }
    .tabs ul {
        justify-content: center;
    }
</style>

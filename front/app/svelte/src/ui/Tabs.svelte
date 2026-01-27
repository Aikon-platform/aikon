<script>
    /** @type {{ id: string, label: string }[]} */
    export let tabs = [];
    export let activeTab = tabs[0]?.id ?? "";
</script>

{#if tabs.length > 1}
    <nav class="tabs-bar">
        <div class="tabs">
            <ul>
                {#each tabs as {id, label}}
                    <li class:is-active={activeTab === id}>
                        <a href={null} on:click|preventDefault={() => activeTab = id}>{label}</a>
                    </li>
                {/each}
            </ul>
        </div>
    </nav>
{/if}

<div class="tab-content">
    <slot {activeTab}/>
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

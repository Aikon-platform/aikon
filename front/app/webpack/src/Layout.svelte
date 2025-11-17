<script>
    export let sidebarWidth = "25";
    export const layoutHeight = "90vh";
    export let activeTab = 0;
    export let tabList = [];
</script>

<div class="layout" style="min-height: {layoutHeight};">
    <aside class="sidebar" style="width: {sidebarWidth}%; min-height: {layoutHeight};">
        <slot name="sidebar"/>
    </aside>


    <main class="main-content" style="width: {100-sidebarWidth}%; min-height: {layoutHeight};">
        <nav class="tabs-bar">
            {#if $$slots.tabs}
                <slot name="tabs" {activeTab}/>
            {:else if tabList.length}
                <div class="tabs">
                    <ul>
                        {#each tabList as tab, index}
                            <li class:is-active={activeTab === index}>
                                <a on:click={() => activeTab = index} href="{null}">{tab}</a>
                            </li>
                        {/each}
                    </ul>
                </div>
            {/if}
        </nav>

        <div class="content-area pl-5">
            <slot name="content" {activeTab}/>
        </div>
    </main>
</div>

<style>
    .layout {
        display: flex;
        width: 100vw;
    }

    .sidebar {
        flex-shrink: 0;
        border-right: 1px solid var(--bulma-border-weak);
        background-color: var(--bulma-scheme-main-bis);
        min-width: 250px;
        max-width: 400px;
        z-index: 2;
    }

    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 0;
    }

    .tabs-bar {
        overflow-x: auto;
        overflow-y: hidden;
        flex-shrink: 0;
        white-space: nowrap;
    }

    .tabs-bar::-webkit-scrollbar {
        height: 6px;
    }

    .tabs-bar::-webkit-scrollbar-track {
        background: var(--bulma-scheme-main);
    }

    .tabs-bar::-webkit-scrollbar-thumb {
        background: var(--bulma-border);
        border-radius: 3px;
    }

    .content-area {
        flex: 1;
        padding: 2% 5% 2% 1%;
        overflow: visible;
    }
</style>

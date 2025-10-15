<script>
    export let sidebarWidth = "25";
    export const layoutHeight = "90vh";
    export let activeTab = 0;
</script>

<div class="layout" style="height: {layoutHeight};">
    <aside class="sidebar" style="width: {sidebarWidth}%; height: {layoutHeight};">
        <slot name="sidebar"/>
    </aside>


    <main class="main-content" style="width: {100-sidebarWidth}%; height: {layoutHeight};">
        <nav class="tabs-bar">
            <slot name="tabs" {activeTab}/>
        </nav>

        <div class="content-area">
            <slot name="content" {activeTab}/>
        </div>
    </main>
</div>

<style>
    .layout {
        display: flex;
    }

    .sidebar {
        flex-shrink: 0;
        overflow-y: auto;
        border-right: 1px solid var(--bulma-border-weak);
        background-color: var(--bulma-black-bis);
        left: 0;
        position: absolute;
        min-width: 250px;
        max-width: 400px;
        z-index: 2;
    }

    .main-content {
        flex: 1;
        overflow-y: auto;
        right: 0;
        position: absolute;
        display: flex;
        flex-direction: column;
    }

    .tabs-bar {
        /*border-bottom: 1px solid var(--bulma-border);*/
        /*padding: 0 5% 0 1%;*/
    }

    .content-area {
        flex: 1;
        overflow-y: auto;
        padding: 2% 5% 2% 1%;
    }
</style>

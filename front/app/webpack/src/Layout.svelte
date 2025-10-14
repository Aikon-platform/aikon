<script>
    let sidebarWidth = 300;
    let isResizing = false;

    function startResize() {
        isResizing = true;
    }

    function handleResize(e) {
        if (!isResizing) return;
        sidebarWidth = Math.max(200, Math.min(e.clientX, 600));
    }

    function stopResize() {
        isResizing = false;
    }
</script>

<svelte:window
    on:mousemove={handleResize}
    on:mouseup={stopResize}
/>

<div class="layout">
    <aside class="sidebar" style="width: {sidebarWidth}px">
        <slot name="sidebar"/>
    </aside>

    <div class="resizer" on:mousedown={startResize}/>

    <main class="content">
        <slot name="content"/>
    </main>
</div>

<style>
    .layout {
        display: flex;
        /*position: fixed;*/
        /*min-height: 95vh;*/
        /*left: 0;*/
        /*right: 0;*/
        height: 100vh;
        flex-direction: row;
        justify-content: left;
        overflow: hidden;
    }

    .sidebar {
        flex-shrink: 0;
        overflow-y: auto;
        border-right: 1px solid var(--bulma-border);
        background-color: var(--bulma-scheme-main-bis);
    }

    .content {
        flex: 1;
        overflow-y: auto;
    }

    .resizer {
        width: 4px;
        cursor: col-resize;
        background-color: transparent;
    }

    .resizer:hover {
        background-color: var(--bulma-link);
    }
</style>

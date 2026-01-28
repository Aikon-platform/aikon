<script>
    import { onMount } from 'svelte';
    import Loading from "./Loading.svelte";
    import { activeLayout } from './ui/tabStore.js';

    export let sidebarWidth = "25";
    export const layoutHeight = "90vh";
    export let tabList = {};

    export let topOffsetElement = null;

    function updateTopOffset(element = null) {
        if (!element) {
            element = document.getElementById("navbar");
        }
        document.documentElement.style.setProperty('--top-offset', `${element.offsetHeight}px`);
    }
    updateTopOffset(topOffsetElement)
    onMount(() => {
        activeLayout.init();
        window.addEventListener('popstate', () => activeLayout.init());
        return () => window.removeEventListener('popstate', () => activeLayout.init());
    });
</script>

<Loading/>

<div class="layout" style="min-height: {layoutHeight};">
    <aside class="sidebar" style="width: {sidebarWidth}%; min-height: {layoutHeight};">
        <slot name="sidebar"/>
    </aside>

    <main class="main-content" style="width: {100-sidebarWidth}%; min-height: {layoutHeight};">
        <nav id="tabs" class="tabs-bar">
            {#if $$slots.tabs}
                <slot name="tabs"/>
            {:else if Object.keys(tabList).length}
                <div class="tabs">
                    <ul>
                        {#each Object.entries(tabList) as [tabRef, tabTitle]}
                            <li class:is-active={$activeLayout === tabRef}>
                                <a on:click={() => activeLayout.change(tabRef)} href="{null}">{tabTitle}</a>
                            </li>
                        {/each}
                    </ul>
                </div>
            {/if}
        </nav>

        <div class="content-area pl-5">
            <slot name="content"/>
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

    .content-area {
        flex: 1;
        padding: 2% 5% 2% 1%;
        overflow: visible;
    }
</style>

<script>
    export let sidebarWidth = "25";
    export const layoutHeight = "90vh";
    export let tabList = {};

    let availableTabs = Object.keys(tabList);

    function updateTopOffset(element = null) {
        if (!element) {
            element = document.getElementById("navbar");
        }
        document.documentElement.style.setProperty('--top-offset', `${element.offsetHeight}px`);
    }
    updateTopOffset()

    // import {onMount} from "svelte";
    // let resizeObserver;
    // onMount(() => {
    //     const tabs = document.getElementById("tabs");
    //     updateTopOffset(tabs);
    //
    //     resizeObserver = new ResizeObserver(() => {
    //         updateTopOffset(tabs);
    //     });
    //
    //     if (tabs) {
    //         resizeObserver.observe(tabs);
    //     }
    //
    //     return () => {
    //         if (resizeObserver && tabs) {
    //             resizeObserver.unobserve(tabs);
    //             resizeObserver.disconnect();
    //         }
    //     };
    // });

    $: activeTab = new URLSearchParams(window.location.search).get("tab") ?? availableTabs[0] ?? null;

    function changeTab(tab) {
        if (!availableTabs.includes(tab)) {
            console.warn(`Tab "${tab}" is not available.`);
            return;
        }
        activeTab = tab;
        const url = new URL(window.location);
        url.searchParams.set("tab", tab);
        window.history.pushState({}, "", url);
    }
</script>

<div class="layout" style="min-height: {layoutHeight};">
    <aside class="sidebar" style="width: {sidebarWidth}%; min-height: {layoutHeight};">
        <slot name="sidebar"/>
    </aside>

    <main class="main-content" style="width: {100-sidebarWidth}%; min-height: {layoutHeight};">
        <nav id="tabs" class="tabs-bar">
            {#if $$slots.tabs}
                <slot name="tabs" {activeTab}/>
            {:else if Object.keys(tabList).length}
                <div class="tabs">
                    <ul>
                        {#each Object.entries(tabList) as [tabRef, tabTitle]}
                            <li class:is-active={activeTab === tabRef}>
                                <a on:click={() => changeTab(tabRef)} href="{null}">{tabTitle}</a>
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

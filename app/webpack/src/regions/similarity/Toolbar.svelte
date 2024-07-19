<script>
    import { fly, fade } from 'svelte/transition';
    import * as cat from './similarityCategory';
    import { similarityStore } from "./similarityStore.js";
    const { excludedCategories } = similarityStore;

    let hoveredCategory = null;

    $: categories = [
        { id: 1, title: cat.exactLabel, svg: cat.exactSvg },
        { id: 2, title: cat.partialLabel, svg: cat.partialSvg },
        { id: 3, title: cat.semanticLabel, svg: cat.semanticSvg },
        { id: 4, title: cat.noLabel, svg: cat.noSvg },
        { id: 5, title: cat.userLabel, svg: cat.userSvg },
    ];

    function toggleCategory(categoryId) {
        excludedCategories.update(current => {
            if (current.includes(categoryId)) {
                return current.filter(id => id !== categoryId);
            } else {
                return [...current, categoryId];
            }
        });

        // Update localStorage
        localStorage.setItem('excludedCategories', JSON.stringify($excludedCategories));
    }
</script>

<div class="toolbar" transition:fade={{ duration: 500 }}>
    {#each categories as category}
        <div class="toolbar-item hoverable {$excludedCategories.includes(category.id) ? '' : 'selected'}"
             on:mouseenter={() => hoveredCategory = category.id}
             on:mouseleave={() => hoveredCategory = null}
             on:click={() => toggleCategory(category.id)}
             on:keyup={null}>
            <span class="tool-icon p-1">
                {@html category.svg}
            </span>
            {#if hoveredCategory === category.id}
                <div class="label-container px-2 py-1" transition:fly={{ x: 40, duration: 300 }}>
                    <span class="label">
                        {category.title}
                    </span>
                </div>
            {/if}
        </div>
    {/each}
</div>

<style>
    .toolbar {
        position: fixed;
        left: 0;
        top: 50%;
        z-index: 7;
        transform: translateY(-50%);
        display: flex;
        flex-direction: column;
        border-radius: 0 10px 10px 0;
    }

    .toolbar-item {
        display: flex;
        align-items: center;
        cursor: pointer;
        padding-left: 0.5em;
        padding-right: 0.6em;
        background-color: var(--bulma-background);
        transition: background-color 0.2s ease-in-out;
    }

    /*.toolbar-item:hover {*/
    /*    background: rgba(0, 0, 0, 0.3); !* Semi-transparent black *!*/
    /*    !*transition: mix-blend-mode 0.3s;*!*/
    /*    mix-blend-mode: multiply;*/
    /*}*/

    .toolbar-item:first-child {
        padding-top: 0.25em;
        padding-bottom: 0.125em;
        border-radius: 0 10px 0 0;
    }

    .toolbar-item:last-child {
        padding-top: 0.125em;
        padding-bottom: 0.25em;
        border-radius: 0 0 10px 0;
    }

    .toolbar-item:not(:first-child):not(:last-child) {
        padding-top: 0.125em;
        padding-bottom: 0.125em;
    }

    .toolbar-item.selected {
        background-color: var(--bulma-link);
    }

    .tool-icon {
        background: none;
        border: none;
    }

    .label-container {
        position: absolute;
        transform: translateX(35px);
        background-color: rgba(0, 0, 0, 0.7);
        border-radius: 4px;
    }

    .label {
        white-space: nowrap;
        color: white;
        font-size: 0.9em;
    }
</style>

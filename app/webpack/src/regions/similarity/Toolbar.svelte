<script>
    import { fly } from 'svelte/transition';
    import * as cat from './similarityCategory';

    let hoveredCategory = null;
    $: showNoMatch = true

    $: categories = [
        { id: 1, title: cat.exactLabel, svg: cat.exactSvg },
        { id: 2, title: cat.partialLabel, svg: cat.partialSvg },
        { id: 3, title: cat.semanticLabel, svg: cat.semanticSvg },
        { id: 4, title: cat.noLabel, svg: cat.noSvg },
        { id: 5, title: cat.userLabel, svg: cat.userSvg },
        { id: 6, title: showNoMatch ? cat.hideLabel : cat.showLabel, svg:  showNoMatch ? cat.hideSvg : cat.showSvg },
    ];

    function toggleNoMatch() {
        showNoMatch = !showNoMatch;
        // TODO: implement
    }
</script>

<div class="toolbar is-contrasted pb-3 pl-3 pr-4">
    {#each categories as category}
        <div class="toolbar-item"
             on:mouseenter={() => hoveredCategory = category.id}
             on:mouseleave={() => hoveredCategory = null}
             on:click={category.id === 6 ? toggleNoMatch() : null}
             on:keyup={null}>
            <span class="tool-icon is-hoverable p-1">
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
        gap: 10px;
        border-radius: 0 10px 10px 0;
    }

    .toolbar-item {
        display: flex;
        align-items: center;
    }

    .tool-icon {
        background: none;
        border: none;
        cursor: pointer;
    }

    .label-container {
        position: absolute;
        transform: translateY(25%) translateX(35px);
        background-color: rgba(0, 0, 0, 0.7);
        border-radius: 4px;
    }

    .label {
        white-space: nowrap;
        color: white;
        font-size: 0.9em;
    }
</style>

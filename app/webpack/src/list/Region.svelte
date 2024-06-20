<script>
    import {refToIIIF} from "../utils.js";
    import {createEventDispatcher} from "svelte";

    const dispatch = createEventDispatcher();

    function toggleSelection(block) {
        dispatch('toggleSelection', { block });
    }

    function copyRegionId() {
        navigator.clipboard.writeText(`${block.img}_${block.xyhw}`);
        // animate
    }

    export let block;
    export let isSelected = false;
</script>

<style>
    svg {
        height: 1em;
        overflow: visible;
        vertical-align: -.125em;
    }
    svg > path {
        transition: fill 0.1s ease-out;
        fill: var(--bulma-link);
    }
    .check-btn {
        position: absolute;
        top: -10px;
        right: -10px;
        z-index: 1;
        padding: 0.5em;
    }
    .card {
        overflow: hidden;
    }
    figure {
        transition: outline 0.1s ease-out;
        outline: 0 solid var(--bulma-link);
    }
    .checked > figure {
        outline: 3px solid var(--bulma-link);
        border-radius: var(--bulma-card-radius);
    }
    .region {
        cursor: pointer;
    }
</style>

<div class="region image is-96x96 {isSelected ? 'checked' : ''}"
     tabindex="-1"
     on:click={() => toggleSelection(block)}
     on:keyup={(event) => event.key === 'Enter' && toggleSelection(block)}>
    <figure id="region-{block.id}" class="image is-96x96 card">
        <img src="{refToIIIF(block.metadata.img, block.metadata.xyhw, '96,')}" alt="Extracted region"/>
    </figure>
    <button class="button check-btn tag">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
            {#if isSelected}
                <path fill="currentColor" d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"/>
            {:else}
                <path fill="currentColor" d="M0 48C0 21.5 21.5 0 48 0l0 48V441.4l130.1-92.9c8.3-6 19.6-6 27.9 0L336 441.4V48H48V0H336c26.5 0 48 21.5 48 48V488c0 9-5 17.2-13 21.3s-17.6 3.4-24.9-1.8L192 397.5 37.9 507.5c-7.3 5.2-16.9 5.9-24.9 1.8S0 497 0 488V48z"/>
            {/if}
        </svg>
    </button>
</div>

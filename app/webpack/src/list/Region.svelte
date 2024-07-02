<script>
    import { fade } from 'svelte/transition';
    import {refToIIIF} from "../utils.js";
    import {createEventDispatcher} from "svelte";

    const dispatch = createEventDispatcher();
    export let block;
    export let isSelected = false;
    export let isCopied = false;
    export let appLang = 'en';

    function toggleSelection() {
        dispatch('toggleSelection', { block });
    }
    function copyRef() {
        dispatch('copyRef', { block });
    }
</script>

<style>
    svg > path {
        transition: fill 0.1s ease-out;
        fill: var(--bulma-link);
    }
    .overlay {
        font-size: 75%;
    }
    figure {
        transition: outline 0.1s ease-out;
        outline: 0 solid var(--bulma-link);
    }
    .checked > figure {
        outline: 4px solid var(--bulma-link);
        border-radius: var(--bulma-card-radius);
    }
    .region {
        cursor: pointer;
        position: relative;
    }
    .tooltip {
        visibility: hidden;
        background-color: rgba(0, 0, 0, 0.7);
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .region-btn:hover .tooltip {
        visibility: visible;
        opacity: 1;
    }
</style>

<div class="region image is-96x96 is-center {isSelected ? 'checked' : ''}" transition:fade={{ duration: 500 }}>
    <figure class="image is-96x96 card" tabindex="-1"
            on:click={() => toggleSelection()} on:keyup={() => null}>
        <img src="{refToIIIF(block.img, block.xyhw, '96,')}" alt="Extracted region"/>
        <div class="overlay is-center">
            <span class="overlay-desc">{block.title}</span>
        </div>
    </figure>
    <button class="button region-btn tag" on:click={() => copyRef()}>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
            {#if isCopied}
                <path d="M208 0H332.1c12.7 0 24.9 5.1 33.9 14.1l67.9 67.9c9 9 14.1 21.2 14.1 33.9V336c0 26.5-21.5 48-48 48H208c-26.5 0-48-21.5-48-48V48c0-26.5 21.5-48 48-48zM48 128h80v64H64V448H256V416h64v48c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V176c0-26.5 21.5-48 48-48z"/>
            {:else}
                <path d="M384 336H192c-8.8 0-16-7.2-16-16V64c0-8.8 7.2-16 16-16l140.1 0L400 115.9V320c0 8.8-7.2 16-16 16zM192 384H384c35.3 0 64-28.7 64-64V115.9c0-12.7-5.1-24.9-14.1-33.9L366.1 14.1c-9-9-21.2-14.1-33.9-14.1H192c-35.3 0-64 28.7-64 64V320c0 35.3 28.7 64 64 64zM64 128c-35.3 0-64 28.7-64 64V448c0 35.3 28.7 64 64 64H256c35.3 0 64-28.7 64-64V416H272v32c0 8.8-7.2 16-16 16H64c-8.8 0-16-7.2-16-16V192c0-8.8 7.2-16 16-16H96V128H64z"/>
            {/if}
        </svg>
        <span class="tooltip">
            {#if isCopied}
                {appLang === 'en' ? "Copied!" : 'Copié !'}
            {:else}
                {appLang === 'en' ? "Copy ID" : "Copier l'ID"}
            {/if}
        </span>
    </button>
</div>

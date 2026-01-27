<script>
    import { createEventDispatcher } from "svelte";
    import { fade } from 'svelte/transition';
    import { appLang } from '../constants';
    import { RegionItem } from "./types.js";
    import { regionsStore } from "./regionsStore.js";
    import { regionsSelection } from "../selection/selectionStore.js";
    import ModalOpener from "./modal/ModalOpener.svelte";
    const { clipBoard } = regionsStore;

    export let selectionStore;
    if (!selectionStore) {
        selectionStore = regionsSelection;
    }
    export let toggleSelection = selectionStore.toggle;

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let item;
    /** @type {number|null} */
    export let index = null;
    /** @type {boolean} */
    export let selected = false;
    /** @type {string|null} */
    export let borderColor = null;
    /** @type {boolean} */
    export let copyable = false;
    /** @type {boolean} */
    export let isInModal = false;
    /** @type {boolean} */
    export let selectable = !isInModal;
    /** @type {boolean} */
    export let isSquare = false;
    /** @type {number|"full"} */
    export let height = isSquare ? 96 : 140;
    if ( height === "full" ) { isSquare = false }

    $: currentRegion = new RegionItem(item);
    $: isCopied = currentRegion.ref === $clipBoard;
    $: imgSrc = currentRegion.url(null, height === "full" ? "full" : isSquare ? `${height},` : `,${height}`);

    const dispatch = createEventDispatcher();
    const openModal = () => isInModal ? null : dispatch("openModal", { index });
</script>

<div class="region is-center" class:checked={selected} style="{height === 'full' ? 'height: 100%' : ''}" transition:fade={{ duration: 10 }}> <!-- -->
    <figure class="image card region-image {isSquare ? 'is-96x96' : ''}" tabindex="-1"
            style="{height === 'full' ? 'height: 100%' : `height: ${height}px; min-width: ${height}px`}; {borderColor ? `border: 5px solid ${borderColor};` : ''}"
            on:click={() => selectable ? toggleSelection(currentRegion) : openModal()} on:keyup={null}>
        <img class="region-img" src={imgSrc} alt="Extracted region"/>
        <div class="overlay is-center">
            <span class="overlay-desc">{@html currentRegion.title}</span>
        </div>
    </figure>

    <div class="region-btn ml-1">
        {#if copyable}
        <button class="button tag" on:click|stopPropagation={() => regionsStore.copyRef(item.ref)}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                {#if isCopied}
                    <path d="M208 0H332.1c12.7 0 24.9 5.1 33.9 14.1l67.9 67.9c9 9 14.1 21.2 14.1 33.9V336c0 26.5-21.5 48-48 48H208c-26.5 0-48-21.5-48-48V48c0-26.5 21.5-48 48-48zM48 128h80v64H64V448H256V416h64v48c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V176c0-26.5 21.5-48 48-48z"/>
                {:else}
                    <path d="M384 336H192c-8.8 0-16-7.2-16-16V64c0-8.8 7.2-16 16-16l140.1 0L400 115.9V320c0 8.8-7.2 16-16 16zM192 384H384c35.3 0 64-28.7 64-64V115.9c0-12.7-5.1-24.9-14.1-33.9L366.1 14.1c-9-9-21.2-14.1-33.9-14.1H192c-35.3 0-64 28.7-64 64V320c0 35.3 28.7 64 64 64zM64 128c-35.3 0-64 28.7-64 64V448c0 35.3 28.7 64 64 64H256c35.3 0 64-28.7 64-64V416H272v32c0 8.8-7.2 16-16 16H64c-8.8 0-16-7.2-16-16V192c0-8.8 7.2-16 16-16H96V128H64z"/>
                {/if}
            </svg>
            <span class="tooltip">
                {#if isCopied}
                    {appLang === 'en' ? "Copied!" : 'Copié !'}
                {:else}
                    {appLang === 'en' ? "Copy ID" : "Copier l'ID"}
                {/if}
            </span>
        </button>
        {/if}
        {#if !isInModal}
            <ModalOpener on:open={openModal}/>
        {/if}
        <slot name="actions"/>
    </div>
</div>

<style>
    .region.checked figure {
        outline: 5px solid var(--bulma-link);
    }
    figure {
        transition: outline 0.1s ease-out;
        margin-bottom: calc(var(--bulma-block-spacing)/2);
    }
    .overlay {
        font-size: 75%;
    }
    .region-img {
        object-fit: contain;
        height: 100%;
    }
    svg > path {
        transition: fill 0.1s ease-out;
        fill: var(--bulma-link);
    }
</style>

<script>
    import { getContext, setContext } from "svelte";
    import { fade } from 'svelte/transition';

    import { refToIIIF } from "../utils.js";
    import { selectionStore } from '../selection/selectionStore.js';
    const { isSelected } = selectionStore;
    import { regionsStore } from './regionsStore.js';
    const { clipBoard } = regionsStore;
    import { appLang } from '../constants';

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let item;
    /** @type {boolean}*/
    export let isSquare = true;
    /** @type {boolean} should not be used in conjunction with isSquare */
    export let isFull = false;
    /** @type {number|string} either a dimension in pixels, or the "full" keyword used by the IIIF image api */
    export let height = isFull ? "full" : isSquare ? 96 : 140;
    /** @type {string}*/
    export let desc = item.title;
    /** @type {Promise<string>?}*/
    export let descPromise = undefined;
    /** @type {string?} used to pass the props `SimilarRegion.qImg` to `ModalController.compareImg`, undefined if `Region` doesn't inherit from `SimilarRegion` */
    export let compareImg = undefined;

    // MoalController is only mountd+imported if !isInModal to avoid a recursive component (Region could open a modal that could contain Region that could contain another modal). while there's no error, you do get a svelte/roillup warning and there probably will be side effects.
    const isInModal = getContext("isInModal") || false;
    let modalControllerComponent;
    if ( !isInModal ) {
        import("./modal/ModalController.svelte").then((res) => modalControllerComponent = res.default);
    }

    $: isCopied = item.ref === $clipBoard;

    // if `descPromise` is passed, wait for resolution to update `desc`
    if (descPromise) {
        descPromise.then((res) => desc = res);
    }



</script>

<div class="region is-center {$isSelected(item) ? 'checked' : ''}" transition:fade={{ duration: 500 }}>
    <figure class="image card region-image {isSquare ? 'is-96x96' : ''}"
            tabindex="-1"
            style="height: {height}px; min-width: {height}px;"
            on:click={() => selectionStore.toggle(item)} on:keyup={() => null}>
        <img class="region-img" src="{refToIIIF(item.img, item.xyhw, isSquare ? '96,' : `,${height}`)}"
             alt="Extracted region"/>
        <div class="overlay is-center">
            <span class="overlay-desc">{@html desc}</span>
        </div>
    </figure>
    <div class="region-btn">
        <button class="button tag" on:click={() => regionsStore.copyRef(item.ref)}>
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
        {#if modalControllerComponent}
            <svelte:component this={modalControllerComponent}
                              mainImg={item.img}
                              compareImg={compareImg}
            ></svelte:component>
        {/if}
    </div>
</div>

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
        /*overflow: hidden;*/
    }
    .checked > figure {
        outline: 4px solid var(--bulma-link);
        border-radius: var(--bulma-card-radius);
    }
    .region-img {
        object-fit: contain;
        height: 100%;
    }
    .region {
        cursor: pointer;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .tooltip {
        visibility: hidden;
        background-color: rgba(0, 0, 0, 0.7);
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 6;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .region-btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-around;
    }
    .region-btn > * {
        width: 100%;
    }
    .region-btn > :first-child {
        margin-bottom: .5em;
    }
    .region-btn >.button:hover .tooltip {
        visibility: visible;
        opacity: 1;
    }
</style>

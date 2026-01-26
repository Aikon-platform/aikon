<script>
    import { getContext } from "svelte";
    import { fade } from 'svelte/transition';

    import { appLang } from '../constants';
    import { regionsSelection } from '../selection/selectionStore.js';

    export let selectionStore;
    if (!selectionStore) {
        selectionStore = regionsSelection;
    }
    const { isSelected } = selectionStore;

    import { regionsStore } from './regionsStore.js';
    const { clipBoard } = regionsStore;

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */
    import { RegionItem } from "./types.js";

    /////////////////////////////////////////////

    /** @type {RegionItemType} */
    export let item;
    /** @type {RegionItemType[]} Optional: array for modal navigation */
    export let items = null;
    /** @type {number} Optional: current index in items */
    export let index = null;
    /** @type {Promise<string>?} */
    export let descPromise = undefined;
    /** @type {boolean} enforce a small square display. if `height === "full"`, will be switched to `false`. see below */
    export let isSquare = true;
    /** @type {number|"full"} either a dimension in pixels, or the "full" keyword used by the IIIF image api */
    export let height = isSquare ? 96 : 140;
    if ( height === "full" ) { isSquare = false } // TODO apparently never true taking previous line into account
    export let borderColor = null;

    export let toggleSelection = selectionStore.toggle;

    /////////////////////////////////////////////
    /** @type {RegionItemType?} defined in `SimilarityRow`.
     * In descendants of `SimilarityRow`, `Region` displays similarity images.
     * This context stores the query image to pass it to `ModalController` */
    const compareImgItem = getContext("qImgMetadata") || undefined;

    const isInModal = getContext("isInModal") || false;

    // disable transitions in modals. else, the new element is mounted before the previous one is unmounted, and it makes a buggy display
    const transitionDuration = isInModal ? 0 : 500;

    // `ModalController` is only mounted+imported if `!isInModal` to avoid a recursive component
    // (`Region` could open a modal that could contain Region that could contain another modal).
    // While there's no error, you do get a svelte/rollup warning and there probably will be side effects.
    let modalControllerComponent;
    if ( !isInModal ) {
        import("./modal/ModalController.svelte").then((res) => modalControllerComponent = res.default);
    }

    export let selectable = !isInModal;
    export let copyable = true;

    item = new RegionItem(item); // instanciate to ensure homogeneous properties

    $: desc = item.title;
    $: if (descPromise) {
        descPromise.then((res) => desc = res);
    }

    $: imgSrc = item.url(null, height === "full" ? height : isSquare ? `${height},` : `,${height}`)
    $: isCopied = item.ref === $clipBoard;
</script>

<div class="region is-center {selectable && $isSelected(item) ? 'checked' : ''}"
     transition:fade={{ duration: transitionDuration }}
     style="{height==='full' ? 'height: 100%' : ''}">
    <figure class="image card region-image {isSquare ? 'is-96x96' : ''}" tabindex="-1"
            style="{height==='full' ? 'height: 100%' : `height: ${height}px; min-width: ${height}px`}; {borderColor ? `border: 5px solid ${borderColor};` : ''}"
            on:click={() => selectable ? toggleSelection(item) : null} on:keyup={() => null}>
        <img class="region-img" src={imgSrc} alt="Extracted region"/>
        <div class="overlay is-center">
            <span class="overlay-desc">{@html desc}</span>
        </div>
    </figure>

    <div class="region-btn ml-1">
        <button class="button tag" on:click={() => copyable ? regionsStore.copyRef(item.ref) : null}
                style="{copyable ? '' : 'display: none;'}">
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
        {#if modalControllerComponent}
            <svelte:component this={modalControllerComponent}
                              mainImgItem={item} compareImgItem={compareImgItem}
                              {items} {index}/>
        {/if}
    </div>
</div>

<style>
    svg > path {
        transition: fill 0.1s ease-out;
        fill: var(--bulma-link);
    }
    .region {
        cursor: pointer;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: start;
        max-height: 100%;
    }
    .region-btn {
        position: relative;
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
    .region-btn > .button:hover .tooltip {
        visibility: visible;
        opacity: 1;
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

    figure {
        transition: outline 0.1s ease-out;
        /*outline: 0 solid var(--bulma-link);*/
        margin-bottom: calc(var(--bulma-block-spacing)/2);  /** divide default margin bottom by 2 */
        /*overflow: hidden;*/
    }
    .overlay {
        font-size: 75%;
    }
    .region-img {
        object-fit: contain;
        height: 100%;
    }
</style>

<script>
    import { run, stopPropagation } from 'svelte/legacy';

    import { createEventDispatcher } from "svelte";
    import { RegionItem } from "./types.js";
    import { regionsStore } from "./regionsStore.js";
    import { regionsSelection } from "../selection/selectionStore.js";
    import ModalOpener from "./modal/ModalOpener.svelte";
    import {i18n, loadWitnessTitle, witnessTitles} from "../utils.js";
    const { clipBoard } = regionsStore;

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */

    /**
     * @typedef {Object} Props
     * @property {any} selectionStore
     * @property {any} [toggleSelection]
     * @property {RegionItemType} item
     * @property {number|null} [index]
     * @property {string|null} [borderColor]
     * @property {int|null} [borderWidth]
     * @property {boolean} [copyable]
     * @property {boolean} [isInModal]
     * @property {boolean} [selectable]
     * @property {boolean} [isSquare]
     * @property {number|"full"} [height]
     * @property {any} [url]
     * @property {any} [downloadable]
     * @property {import('svelte').Snippet} [actions]
     */

    /** @type {Props} */
    let {
        selectionStore = $bindable(regionsSelection),
        toggleSelection = (...args) => selectionStore.toggle(...args),
        item,
        index = null,
        borderColor = null,
        borderWidth = 5,
        copyable = false,
        isInModal = false,
        selectable = !isInModal,
        isSquare = $bindable(false),
        height = isSquare ? 96 : 140,
        url = null,
        downloadable = isInModal,
        actions
    } = $props();

    if ( height === "full" ) { isSquare = false }
    const { isSelected } = selectionStore;

    let currentRegion = $derived(new RegionItem(item));
    let isCopied = $derived(currentRegion.copyId === $clipBoard);
    let imgSrc = $derived(url ?? currentRegion.url(null, height === "full" ? "full" : isSquare ? `${height},` : `,${height}`));
    run(() => {
        isInModal && loadWitnessTitle(currentRegion.witnessId);
    });

    const dispatch = createEventDispatcher();
    const openModal = () => isInModal ? null : dispatch("openModal", { index });

    const download = async () => {
        const res = await fetch(currentRegion.url(null, "full"));
        const url = URL.createObjectURL(await res.blob());
        Object.assign(document.createElement("a"), { href: url, download: `${currentRegion.ref.replace(".jpg", "")}.jpg` }).click();
        URL.revokeObjectURL(url);
    };

    const t = {
        downloadImg: { en: "Download image", fr: "Télécharger l'image" },
        copy: { en: "Copy ID", fr: "Copier l'ID" },
        copied: { en: "Copied!", fr: "Copié !" },
    };
</script>

<div class="region is-center {selectable && $isSelected(item) ? 'checked' : ''}" style="{height === 'full' ? 'height: 100%' : ''}">
    <figure class="image card region-image" class:is-96x96={isSquare} tabindex="-1"
            style="{height === 'full' ? 'height: 100%' : `height: ${height}px; min-width: ${height}px`}; {borderColor ? `border: ${borderWidth}px solid ${borderColor};` : ''}"
            onclick={() => selectable ? toggleSelection(currentRegion) : openModal()} onkeyup={null}>
        <img class="region-img" src={imgSrc} alt="Extracted region" loading="lazy"/>
        <div class="overlay is-center">
            <span class="overlay-desc">{@html isInModal ? currentRegion.label($witnessTitles[currentRegion.witnessId]) : currentRegion.title}</span>
        </div>
    </figure>

    <div class="region-btn ml-1">
        {#if copyable}
        <button class="button tag" onclick={stopPropagation(() => regionsStore.copyRef(currentRegion.copyId))}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                {#if isCopied}
                    <path d="M208 0H332.1c12.7 0 24.9 5.1 33.9 14.1l67.9 67.9c9 9 14.1 21.2 14.1 33.9V336c0 26.5-21.5 48-48 48H208c-26.5 0-48-21.5-48-48V48c0-26.5 21.5-48 48-48zM48 128h80v64H64V448H256V416h64v48c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V176c0-26.5 21.5-48 48-48z"/>
                {:else}
                    <path d="M384 336H192c-8.8 0-16-7.2-16-16V64c0-8.8 7.2-16 16-16l140.1 0L400 115.9V320c0 8.8-7.2 16-16 16zM192 384H384c35.3 0 64-28.7 64-64V115.9c0-12.7-5.1-24.9-14.1-33.9L366.1 14.1c-9-9-21.2-14.1-33.9-14.1H192c-35.3 0-64 28.7-64 64V320c0 35.3 28.7 64 64 64zM64 128c-35.3 0-64 28.7-64 64V448c0 35.3 28.7 64 64 64H256c35.3 0 64-28.7 64-64V416H272v32c0 8.8-7.2 16-16 16H64c-8.8 0-16-7.2-16-16V192c0-8.8 7.2-16 16-16H96V128H64z"/>
                {/if}
            </svg>
            <span class="tooltip">
                {i18n(isCopied ? "copied" : "copy", t)}
            </span>
        </button>
        {/if}
        {#if !isInModal}
            <ModalOpener on:open={openModal}/>
        {/if}
        {#if downloadable}
            <button class="button tag mb-1 p-0 p-2 has-text-link" onclick={stopPropagation(download)} title={i18n("downloadImg", t)}>
                <i class="fa-solid fa-download"></i>
            </button>
        {/if}
        {@render actions?.()}
    </div>
</div>

<style>
    .region.checked figure {
        outline: 4px solid var(--bulma-link);
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
        max-height: 60vh;
    }
    svg > path {
        transition: fill 0.1s ease-out;
        fill: var(--bulma-link);
    }
</style>

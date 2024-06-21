<script>
    import Region from './Region.svelte';
    import {saveSelection, emptySelection, addToSelection, removeFromSelection} from "./selection.js";
    import SelectionBtn from "./SelectionBtn.svelte";
    import SelectionFooter from "./SelectionFooter.svelte";
    import {manifestToMirador, refToIIIF} from "../utils.js";

    let addAnimation = false;
    let removeAnimation = false;
    export const regionsType = "Regions"
    export let regions = {};
    export let appLang = 'en';
    export let manifest = '';

    let selection = JSON.parse(localStorage.getItem("documentSet")) ?? {};
    $: selectionLength = selection.hasOwnProperty(regionsType) ? Object.keys(selection[regionsType]).length : 0;
    $: isBlockSelected = (block) => selection[regionsType]?.hasOwnProperty(block.id);
    $: areSelectedRegions = Object.keys(selection[regionsType] ?? {}).length > 0;

    $: console.log(regions);

    function handleCommitSelection(event) {
        const { updateType } = event.detail;
        if (updateType === 'clear') {
            selection = emptySelection(selection, [regionsType]);
        } else if (updateType === 'save') {
            selection = saveSelection(selection);
        }
    }

    function removeRegion(blockId) {
        selection = removeFromSelection(selection, blockId, regionsType);
        removeAnimation = true;
        setTimeout(() => removeAnimation = false, 300);
    }

    function addRegion(block) {
        selection = addToSelection(selection, block);
        addAnimation = true;
        setTimeout(() => addAnimation = false, 300);
    }

    function handleToggleSelection(event) {
        const { block } = event.detail;
        if (!isBlockSelected(block)) {
            addRegion(block);
        } else {
            removeRegion(block.id);
        }
    }

    $: clipBoard = "";
    // TODO: isBlockCopied stays to true if user copied another string
    $: isBlockCopied = (block) => clipBoard === block.id;
    function handleCopyId(event) {
        const { block } = event.detail;
        const blockId = isBlockCopied(block) ? "" : block.id;
        navigator.clipboard.writeText(blockId);
        clipBoard = blockId;
    }

    const layouts = {
        all: { text: appLang === 'en' ? 'All regions' : 'Toutes les régions' },
        page: { text: appLang === 'en' ? 'Per page' : 'Par page' },
        similarity: { text: appLang === 'en' ? 'Similarity' : 'Similarité' }
    }
    $: selectedLayout = "all"

    $: isEditMode = false;
</script>

<style>
    .selection {
        position: relative;
        width: 64px;
    }
    .overlay {
        font-size: 50%;
    }
    path {
        fill: currentColor;
    }
    .edit-action {
        height: 2em;
    }
    .center-flex {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .actions {
        align-items: flex-end;
    }
    .center-flex > div {
        margin-bottom: 1em;
    }
</style>

<SelectionBtn {addAnimation} {removeAnimation} {selectionLength} {appLang} />

<div class="is-left center-flex actions">
    <div>
        <button class="button {isEditMode ? 'is-success' : 'is-link'} mr-3" on:click={() => isEditMode = !isEditMode}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" class="pr-3">
                {#if isEditMode}
                    <!--Check icon-->
                    <path d="M438.6 105.4c12.5 12.5 12.5 32.8 0 45.3l-256 256c-12.5 12.5-32.8 12.5-45.3 0l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0L160 338.7 393.4 105.4c12.5-12.5 32.8-12.5 45.3 0z"/>
                {:else}
                    <!--Edit icon-->
                    <path d="M471.6 21.7c-21.9-21.9-57.3-21.9-79.2 0L362.3 51.7l97.9 97.9 30.1-30.1c21.9-21.9 21.9-57.3 0-79.2L471.6 21.7zm-299.2 220c-6.1 6.1-10.8 13.6-13.5 21.9l-29.6 88.8c-2.9 8.6-.6 18.1 5.8 24.6s15.9 8.7 24.6 5.8l88.8-29.6c8.2-2.7 15.7-7.4 21.9-13.5L437.7 172.3 339.7 74.3 172.4 241.7zM96 64C43 64 0 107 0 160V416c0 53 43 96 96 96H352c53 0 96-43 96-96V320c0-17.7-14.3-32-32-32s-32 14.3-32 32v96c0 17.7-14.3 32-32 32H96c-17.7 0-32-14.3-32-32V160c0-17.7 14.3-32 32-32h96c17.7 0 32-14.3 32-32s-14.3-32-32-32H96z"/>
                {/if}
            </svg>
            {#if isEditMode}{appLang === 'en' ? 'Validate' : 'Valider'}{:else}{appLang === 'en' ? 'Edit' : 'Modifier'}{/if}
        </button>
        <button class="button is-link is-light mr-3" on:click={() => null}>
            <i class="fa-solid fa-square-check"></i>
            {appLang === 'en' ? 'Select all' : 'Tout sélectionner'}
        </button>
        <button class="button is-link is-light" on:click={() => null}>
            <i class="fa-solid fa-download"></i>
            {appLang === 'en' ? 'Download' : 'Télecharger'}
        </button>
    </div>

    <div class="edit-action">
        {#if isEditMode}
            <button class="tag is-link is-light is-rounded mr-3">
                <i class="fa-solid fa-rotate-right"></i>
                {appLang === 'en' ? 'Reload' : "Recharger"}
            </button>
            <a class="tag is-link is-rounded mr-3" href="{manifestToMirador(manifest)}" target="_blank">
                <i class="fa-solid fa-edit"></i>
                {appLang === 'en' ? 'Go to editor' : "Aller à l'éditeur"}
            </a>
            <button class="tag is-danger is-rounded">
                <i class="fa-solid fa-trash"></i>
                {appLang === 'en' ? 'Delete selected regions' : 'Supprimer les regions selectionnées'}
            </button>
        {/if}
    </div>
</div>



<div class="tabs is-centered">
    <ul class="panel-tabs">
        {#each Object.entries(layouts) as [layout, meta]}
            <li class:is-active={layout === selectedLayout}
                on:click={() => selectedLayout = layout} on:keyup={() => null}>
                <a>{meta.text}</a>
            </li>
        {/each}
    </ul>
</div>

{#if selectedLayout === "all"}
    <div class="fixed-grid has-auto-count">
        <div class="grid is-gap-2">
            {#each Object.values(regions).flat(1) as block (block.id)}
                <Region {block} {appLang}
                        isSelected={isBlockSelected(block)}
                        isCopied={isBlockCopied(block)}
                        on:toggleSelection={handleToggleSelection}
                        on:copyId={handleCopyId}/>
            {:else}
                <!--TODO Create manual annotation btn-->
                <!--TODO if extraction app installed, add btn for annotation request-->
                NO ANNOTATION
            {/each}
        </div>
    </div>
{:else if selectedLayout === "page"}
    <table class="table">
        <tbody>
        <!--TODO add way to display all pages (not only pages with annotations)-->
            {#each Object.entries(regions) as [canvasNb, blocks]}
                <tr>
                    <th class="is-3 is-dark center-flex">
                        <img src="{refToIIIF(blocks[0].img, 'full', '250,')}" alt="Canvas {canvasNb}" class="mb-3">
                        <div class="is-center mb-1">
                            <a class="tag px-2 py-1 is-rounded" href="{manifestToMirador(manifest, canvasNb)}" target="_blank">
                                <i class="fa-solid fa-pen-to-square"></i>
                                Page {canvasNb}
                            </a>
                        </div>
                    </th>
                    <td class="is-fullwidth">
                        <div class="fixed-grid has-auto-count">
                            <div class="grid is-gap-2">
                                {#each blocks as block (block.id)}
                                    <Region {block} {appLang}
                                            isSelected={isBlockSelected(block)}
                                            isCopied={isBlockCopied(block)}
                                            on:toggleSelection={handleToggleSelection}
                                            on:copyId={handleCopyId}/>
                                {/each}
                            </div>
                        </div>
                    </td>
                </tr>
            {:else}
                <tr>NO ANNOTATION</tr>
                <!--TODO Create manual annotation btn-->
                <!--TODO if extraction app installed, add btn for annotation request-->
            {/each}
        </tbody>
    </table>
{:else if selectedLayout === "similarity"}
    <div>tout doux</div>
{/if}

<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"></div>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <i class="fa-solid fa-book-bookmark"></i>
                {appLang === 'en' ? 'Selected regions' : 'Regions sélectionnées'}
                (<span id="selection-count">{selectionLength}</span>)
            </div>
            <button class="delete media-left" aria-label="close"></button>
        </div>
        <section class="modal-card-body">
            {#if areSelectedRegions}
                <div class="fixed-grid has-6-cols">
                    <div class="grid is-gap-2">
                        {#each Object.entries(selection[regionsType]) as [id, meta]}
                            <div class="selection cell">
                                <figure class="image is-64x64 card">
                                    <img src="{refToIIIF(meta.img, meta.xyhw, '96,')}" alt="Extracted region"/>
                                    <div class="overlay is-center">
                                        <span class="overlay-desc">{meta.title}</span>
                                    </div>
                                </figure>
                                <button class="delete region-btn" aria-label="remove from selection" on:click={() => removeRegion(id)}></button>
                            </div>
                        {/each}
                    </div>
                </div>
            {:else}
                <div>
                    {appLang === 'en' ? 'No regions in selection' : 'Aucune région sélectionnée'}
                </div>
            {/if}
        </section>
        <SelectionFooter {appLang} on:commitSelection={handleCommitSelection}/>
    </div>
</div>

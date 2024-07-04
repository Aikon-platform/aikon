<script>
    import {manifestToMirador, refToIIIF, showMessage} from "../utils.js";
    import { selectionStore } from './stores/selectionStore.js';
    const { selected, nbSelected } = selectionStore;
    import { writable } from 'svelte/store';

    import Region from './Region.svelte';
    import SelectionBtn from "./SelectionBtn.svelte";
    import SelectionFooter from "./SelectionFooter.svelte";
    import RegionsRow from "./RegionsRow.svelte";
    import Pagination from "./Pagination.svelte";
    import Modal from "../Modal.svelte";

    export const regionsType = "Regions"
    export let regions = {};
    export let appLang = 'en';
    export let manifest = '';
    export let isValidated = false;
    export let imgPrefix = '';
    export let nbOfPages = 1;
    const zeros = (n, l) => n.toString().padStart(l, '0');

    $: selectedRegions = $selected(true);
    $: selectionLength = Object.keys(selectedRegions).length;

    $: areSelectedRegions = selectionLength > 0;
    $: isEditMode = !isValidated;

    function toImgName(canvasNb){
        return `${imgPrefix}_${zeros(canvasNb, String(nbOfPages).length + 1)}`;
    }

    const layouts = {
        all: { text: appLang === 'en' ? 'All regions' : 'Toutes les régions' },
        page: { text: appLang === 'en' ? 'Per page' : 'Par page' },
        similarity: { text: appLang === 'en' ? 'Similarity' : 'Similarité' },
        vectorization: { text: appLang === 'en' ? 'Vectorization' : 'Vectorisation' }
    }
    $: currentLayout = "all"
    $: baseUrl = `${window.location.origin}${window.location.pathname}`;

    $: currentPage = parseInt(new URLSearchParams(window.location.search).get("p") ?? 1);
    const pageRegions = writable({});
    $: fetchPages = (async () => {
        const response = await fetch(`${baseUrl}canvas?p=${currentPage}`);
        const data = await response.json();
        pageRegions.set(data);
        return data;
    })()

    function handlePageUpdate(event) {
        const { pageNb } = event.detail;
        currentPage = pageNb;
        const url = new URL(baseUrl);
        url.searchParams.set("p", currentPage);
        window.history.pushState({}, '', url);
    }

    function toggleEditMode() {
        isEditMode = !isEditMode;
        // todo send validation status to backend
    }

    async function deleteSelectedRegions() {
        const confirmed = await showMessage(
            appLang === "en" ? "Are you sure you want to delete regions?" : "Voulez-vous vraiment supprimer les régions?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );

        if (!confirmed) {
            return; // User cancelled the deletion
        }

        for (const regionId of Object.keys(selectedRegions)) {
            try {
                if (!regions.hasOwnProperty(regionId)) {
                    // only delete regions that are displayed
                    continue;
                }
                await deleteRegion(regionId);
                delete regions[regionId];
                regions = { ...regions }; // for reactivity

                pageRegions.update(currentPageRegions => {
                    for (const canvasNb in currentPageRegions) {
                        if (currentPageRegions[canvasNb][regionId]) {
                            const { [regionId]: _, ...rest } = currentPageRegions[canvasNb];
                            currentPageRegions[canvasNb] = rest;
                            return currentPageRegions;
                        }
                    }
                    return currentPageRegions;
                });
                selectionStore.remove(regionId, regionsType)

            } catch (error) {
                success = false;
                await showMessage(`Failed to delete region ${regionId}: ${error.message}`, "Error");
            }
        }
    }
    async function deleteRegion(regionId) {
        const HTTP_SAS = SAS_APP_URL.replace("https", "http");
        const urlDelete = `${SAS_APP_URL}/annotation/destroy?uri=${HTTP_SAS}/annotation/${regionId}`;

        const response = await fetch(urlDelete, { method: "DELETE"});

        if (response.status !== 204) {
            throw new Error(`Failed to delete ${urlDelete} due to ${response.status}: '${response.statusText}'`);
        }
    }

    function areAllSelected() {
        // TODO here when there is not only one document selected, this assertion is erroneous
        return selectionLength === Object.keys(regions).length;
    }

    function getSelectBtnLabel(areAllRegionsSelected = null) {
        if (areAllRegionsSelected === null){
            areAllRegionsSelected = areAllSelected()
        }
        if (areAllRegionsSelected) {
            return appLang === 'en' ? 'Unselect all' : 'Tout désélectionner';
        } else {
            return appLang === 'en' ? 'Select all' : 'Tout sélectionner';
        }
    }

    function toggleAllSelection() {
        if (areAllSelected()) {
            selectionStore.removeAll(Object.keys(regions), 'Regions');
        } else {
            selectionStore.addAll(Object.values(regions));
        }
    }

    $: clipBoard = "";
    // TODO: isItemCopied stays to true if user copied another string
    $: isItemCopied = (item) => clipBoard === item.ref;
    function handleCopyRef(event) {
        const { item } = event.detail;
        const itemRef = isItemCopied(item) ? "" : item.ref;
        navigator.clipboard.writeText(itemRef);
        clipBoard = itemRef;
    }
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
    .actions {
        align-items: flex-end;
    }
    .center-flex > div {
        margin-bottom: 1em;
    }
    #nav-actions {
        position: sticky;
        top: 0;
        z-index: 2;
        background-color: var(--bulma-body-background-color);
        box-shadow: var(--bulma-body-background-color) 0 0 25px;
        padding-top: 5em;
        margin-top: -5em;
    }
</style>

<Modal {appLang}/>

<SelectionBtn {selectionLength} {appLang} />

<!--TODO add link to annotations views / for annotation directly, add btn to delete annotation-->

<div id="nav-actions" class="mb-5">
    <div class="center-flex actions">
        <div class="is-left">
            <button class="button {isEditMode ? 'is-success' : 'is-link'} mr-3" on:click={() => toggleEditMode()}>
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
            <button class="button is-link is-light mr-3" on:click={toggleAllSelection}>
                <i class="fa-solid fa-square-check"></i>
                <!--TODO toggle to unselect all if everything is selected-->
                <span id="all-selection">{getSelectBtnLabel()}</span>
            </button>
            <button class="button is-link is-light" on:click={() => null}>
                <i class="fa-solid fa-download"></i>
                {appLang === 'en' ? 'Download' : 'Télecharger'}
            </button>
        </div>

        <div class="edit-action">
            {#if isEditMode}
                <button class="tag is-link is-light is-rounded mr-3" on:click={() => location.reload()}>
                    <i class="fa-solid fa-rotate-right"></i>
                    {appLang === 'en' ? 'Reload' : "Recharger"}
                </button>
                <a class="tag is-link is-rounded mr-3" href="{manifestToMirador(manifest)}" target="_blank">
                    <i class="fa-solid fa-edit"></i>
                    {appLang === 'en' ? 'Go to editor' : "Aller à l'éditeur"}
                </a>
                <button class="tag is-danger is-rounded" on:click={deleteSelectedRegions}>
                    <i class="fa-solid fa-trash"></i>
                    {appLang === 'en' ? 'Delete selected regions' : 'Supprimer les régions sélectionnées'}
                </button>
            {/if}
        </div>
    </div>

    <div class="tabs is-centered">
        <ul class="panel-tabs">
            {#each Object.entries(layouts) as [layout, meta]}
                <!--TODO make active tab appear in url-->
                <li class:is-active={layout === currentLayout}
                    on:click={() => currentLayout = layout} on:keyup={() => null}>
                    <a href={null}>{meta.text}</a>
                </li>
            {/each}
        </ul>
    </div>
</div>


{#if currentLayout === "all"}
        <div class="grid is-gap-2">
            {#each Object.values(regions) as item (item.id)}
                <!--TODO dont sort object keys alphabetically-->
                <Region {item} {appLang}
                        isCopied={isItemCopied(item)}
                        on:copyRef={handleCopyRef}/>
            {:else}
                <!--TODO Create manual annotation btn / import anno file-->
                <!--TODO if extraction app installed, add btn for annotation request-->
                NO ANNOTATION
            {/each}
        </div>
{:else if currentLayout === "page"}
    <!--TODO deduce max page from nbOfPages-->
    <Pagination pageNb={currentPage} maxPage={10} on:pageUpdate={handlePageUpdate}/>
    <table class="table is-fullwidth">
        <tbody>
        {#await fetchPages}
            <tr class="faded is-center">Retrieving paginated regions...</tr>
        {:then _}
            {#if Object.values($pageRegions).length > 0}
                <!--TODO make empty canvases appear-->
                {#each Object.entries($pageRegions) as [canvasNb, items]}
                    <RegionsRow canvasImg={toImgName(canvasNb)} {canvasNb} {manifest}>
                        {#each Object.values(items) as item (item.id)}
                            <Region {item} {appLang}
                                    isCopied={isItemCopied(item)}
                                    on:copyRef={handleCopyRef}/>
                        {/each}
                    </RegionsRow>
                {/each}
            {:else}
                <tr>
                    NO ANNOTATION
                    <!--TODO Create manual annotation btn-->
                    <!--TODO if extraction app installed, add btn for annotation request-->
                </tr>
            {/if}
        {:catch error}
            <tr>Error when retrieving paginated regions: {error}</tr>
        {/await}

        </tbody>
    </table>
{:else if currentLayout === "similarity"}
    <div>tout doux</div>
{:else if currentLayout === "vectorization"}
    <div>tout doux</div>
{/if}

<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"/>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <i class="fa-solid fa-book-bookmark"></i>
                {appLang === 'en' ? 'Selected regions' : 'Regions sélectionnées'}
                ({selectionLength})
            </div>
            <button class="delete media-left" aria-label="close"/>
        </div>
        <section class="modal-card-body">
            {#if areSelectedRegions}
                <div class="fixed-grid has-6-cols">
                    <div class="grid is-gap-2">
                        {#each Object.entries(selectedRegions) as [id, meta]}
                            <div class="selection cell">
                                <figure class="image is-64x64 card">
                                    <img src="{refToIIIF(meta.img, meta.xyhw, '96,')}" alt="Extracted region"/>
                                    <div class="overlay is-center">
                                        <span class="overlay-desc">{meta.title}</span>
                                    </div>
                                </figure>
                                <button class="delete region-btn" aria-label="remove from selection"
                                        on:click={() => selectionStore.remove(id, regionsType)}/>
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
        <SelectionFooter {appLang} isRegion={true}/>
    </div>
</div>

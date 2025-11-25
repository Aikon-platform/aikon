<script>
    import { getContext } from 'svelte';
    import { manifestToMirador, showMessage, downloadBlob, withLoading } from "../utils.js";
    import { selectionStore } from "../selection/selectionStore.js";
    const { selected, nbSelected } = selectionStore;
    import { regionsStore } from './regionsStore.js';
    const { allRegions } = regionsStore;
    import { appName, appLang, regionsType, csrfToken } from '../constants';

    const manifest = getContext('manifest');
    const isValidated = getContext('isValidated');

    console.log(">".repeat(10), manifest);

    $: selectionLength = $nbSelected(true);
    $: isEditMode = !isValidated;
    $: selectedRegions = $selected(true);

    // TODO here when there is not only one document selected, this assertion is erroneous
    $: areAllSelected = selectionLength >= Object.keys($allRegions).length;

    function toggleEditMode() {
        isEditMode = !isEditMode;
        // TODO send validation status to backend
    }

    // TODO add toggle button to switch in between select mode and view mode

    async function deleteSelectedRegions() {
        const confirmed = await showMessage(
            appLang === "en" ? "Are you sure you want to delete these regions?" : "Voulez-vous vraiment supprimer ces régions ?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );

        if (!confirmed) {
            return; // User cancelled the deletion
        }

        for (const regionId of Object.keys(selectedRegions)) {
            try {
                if (!$allRegions.hasOwnProperty(regionId)) {
                    // only delete regions that are displayed
                    continue;
                }
                await deleteRegion(regionId);
                regionsStore.remove(regionId);
                selectionStore.remove(regionId, regionsType)

            } catch (error) {
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

    function toggleAllSelection() {
        if (areAllSelected) {
            selectionStore.removeAll(Object.keys($allRegions), regionsType);
        } else {
            selectionStore.addAll(Object.values($allRegions));
        }
    }

    async function downloadRegions(){
        // download only displayed regions?
        const regionsRef = Object.values($selected(true)).map(r => r.ref);
        const response = await withLoading(() => fetch(`${window.location.origin}/${appName}/regions/export`, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
            body: JSON.stringify({regionsRef})
        }));
        const blob = await response.blob();
        // TODO find better filename
        downloadBlob(blob, 'regions.zip');
    }
</script>

<div class="is-right mb-3">
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
        <!--<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
        {#if areAllSelected}
            <! --Unchecked icon-- >
            <! --<path d="M64 80c-8.8 0-16 7.2-16 16V416c0 8.8 7.2 16 16 16H384c8.8 0 16-7.2 16-16V96c0-8.8-7.2-16-16-16H64zM0 96C0 60.7 28.7 32 64 32H384c35.3 0 64 28.7 64 64V416c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V96zM337 209L209 337c-9.4 9.4-24.6 9.4-33.9 0l-64-64c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l47 47L303 175c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9z"/>-- >
            <path d="m10.6 16.2l7.05-7.05l-1.4-1.4l-5.65 5.65l-2.85-2.85l-1.4 1.4zM5 21q-.825 0-1.412-.587T3 19V5q0-.825.588-1.412T5 3h14q.825 0 1.413.588T21 5v14q0 .825-.587 1.413T19 21zm0-2h14V5H5zM5 5v14z" />
        {:else}
            <! --Checked icon-- >
            <! --<path d="M64 32C28.7 32 0 60.7 0 96V416c0 35.3 28.7 64 64 64H384c35.3 0 64-28.7 64-64V96c0-35.3-28.7-64-64-64H64zM337 209L209 337c-9.4 9.4-24.6 9.4-33.9 0l-64-64c-9.4-9.4-9.4-24.6 0-33.9s24.6-9.4 33.9 0l47 47L303 175c9.4-9.4 24.6-9.4 33.9 0s9.4 24.6 0 33.9z"/>-- >
            <path d="m10.6 16.2l7.05-7.05l-1.4-1.4l-5.65 5.65l-2.85-2.85l-1.4 1.4zM5 21q-.825 0-1.412-.587T3 19V5q0-.825.588-1.412T5 3h14q.825 0 1.413.588T21 5v14q0 .825-.587 1.413T19 21z" />
        {/if}
        </svg>-->
        <i class="fa-solid fa-square-check"></i>
        <span id="all-selection">{appLang === 'en' ? 'Select all' : 'Tout sélectionner'}</span>
    </button>
    <button class="button is-link is-light" on:click={downloadRegions}>
        <i class="fa-solid fa-download"></i>
        {appLang === 'en' ? 'Download' : 'Télécharger'}
    </button>
</div>

<div class="edit-action is-right">
    {#if isEditMode}
        <!--TODO make reload fetch regions with api request-->
        <button class="tag is-link is-light is-rounded mr-3" on:click={() => location.reload()}>
            <i class="fa-solid fa-rotate-right"></i>
            {appLang === 'en' ? 'Reload' : "Recharger"}
        </button>
        <!-- when no regions extraction have been made, we hide the button: "Go to editor" redirects to a Mirador editor for a specific region extraction, which hasn't been created yet -->
        {#if manifest.length}
            <a class="tag is-link is-rounded mr-3" href="{manifestToMirador(manifest)}" target="_blank">
                <i class="fa-solid fa-edit"></i>
                {appLang === 'en' ? 'Go to editor' : "Aller à l'éditeur"}
            </a>
        {/if}
        <button class="tag is-danger is-rounded" on:click={deleteSelectedRegions}>
            <i class="fa-solid fa-trash"></i>
            {appLang === 'en' ? 'Delete selected regions' : 'Supprimer les régions sélectionnées'}
        </button>
    {/if}
</div>

<style>
    .edit-action {
        height: 2em;
    }
    svg > path {
        transition: fill 0.1s ease-out;
        fill: currentColor;
    }
</style>

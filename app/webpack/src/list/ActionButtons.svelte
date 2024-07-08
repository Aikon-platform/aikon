<script>
    import {manifestToMirador, showMessage} from "../utils.js";
    import {selectionStore} from "./stores/selectionStore.js";
    const { selected, nbSelected } = selectionStore;
    import { regionsStore } from './stores/regions.js';
    const { allRegions } = regionsStore;

    export let appLang;
    export let manifest;
    export let isValidated;
    export let regionsType;

    $: selectionLength = $nbSelected(true);
    $: isEditMode = !isValidated;
    $: selectedRegions = $selected(true);

    function toggleEditMode() {
        isEditMode = !isEditMode;
        // todo send validation status to backend
    }

    function areAllSelected() {
        // TODO here when there is not only one document selected, this assertion is erroneous
        return selectionLength === Object.keys($allRegions).length;
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
            selectionStore.removeAll(Object.keys($allRegions), 'Regions');
        } else {
            selectionStore.addAll(Object.values($allRegions));
        }
    }

    function downloadRegions(){
        console.log($selected(true));
    }
</script>

<div class="is-left mb-3">
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
        <span id="all-selection">{getSelectBtnLabel()}</span>
    </button>
    <button class="button is-link is-light" on:click={downloadRegions}>
        <i class="fa-solid fa-download"></i>
        <!-- TODO add download function -->
        {appLang === 'en' ? 'Download' : 'Télécharger'}
    </button>
</div>

<div class="edit-action is-left">
    {#if isEditMode}
        <!--TODO make reload fetch regions with api request-->
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

<style>
    .edit-action {
        height: 2em;
    }
    path {
        fill: currentColor;
    }
</style>

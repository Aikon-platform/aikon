<script>
    import { getContext } from 'svelte';
    import {showMessage, withLoading} from "../utils.js";
    import { appLang, appName, csrfToken } from '../constants';

    const witness = getContext('witness');
    export let baseUrl = `${window.location.origin}${window.location.pathname}`;
    export let currentRegionId;
    export let currentLayout;

    async function deleteRegions() {
        const confirmed = await showMessage(
            appLang === "en" ? "Are you sure you want to delete this record?" : "Voulez-vous vraiment supprimer cet enregistrement ?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );

        if (!confirmed) {
            return;
        }

        if (typeof currentRegionId !== 'number') {
            throw new Error('Invalid region ID');
        }
        const url = `${window.location.origin}/${appName}/regions/${currentRegionId}/delete`;
        try {
            const response = await withLoading(() => fetch(url, {
                method: "DELETE",
                headers: { "X-CSRFToken": csrfToken },
            }));
            if (response.status !== 204) {
                throw new Error(`Failed to delete regions: '${response.statusText}'`);
            }
            window.location.href = `${baseUrl.split('regions/')[0]}regions/`;
        } catch (error) {
            console.error(error);
        }
    }

    async function deleteSimilarity() {
        const confirmed = await showMessage(
            appLang === "en" ? "Are you sure you want to delete all similarity scores for this document?" : "Voulez-vous vraiment supprimer l'intégralité des scores de similarité pour ce document ?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );

        if (!confirmed) {
            return;
        }

        if (typeof currentRegionId !== 'number') {
            throw new Error('Invalid region ID');
        }
        const url = `${window.location.origin}/${appName}/similarity/reset/${currentRegionId}`;
        try {
            const response = await withLoading(() => fetch(url, {
                method: "DELETE",
                headers: { "X-CSRFToken": csrfToken },
            }));
            if (response.status === 204 || response.status === 200) {
                window.location.href = `${baseUrl.split('regions/')[0]}regions/`;
            } else {
                throw new Error(`Failed to delete similarity: '${response.statusText}'`);
            }
        } catch (error) {
            console.error(error);
            await showMessage(error.message, "Error");
        }
    }
</script>

<div>
    {currentLayout}
    {#if currentRegionId}
        {#if ["all", "page"].includes(currentLayout)}
            <button on:click={deleteRegions} class="tag is-danger">
                {appLang === "en" ? "Delete regions record" : "Supprimer l'intégralité des régions"}
            </button>
        {:else if currentLayout === "similarity"}
            <button on:click={deleteSimilarity} class="tag is-danger">
                {appLang === "en" ? "Delete all regions similarity" : "Supprimer toutes les similarités du document"}
            </button>
        {/if}
    {:else}
        {#each witness.regions as regionId}
            <a href="{baseUrl}{regionId}" class="tag is-dark mr-3 is-rounded">Regions #{regionId}</a>
        {/each}
        <!--TODO add NEW REGIONS BUTTON (to create empty region in order to launch new automatic extraction)-->
    {/if}
</div>

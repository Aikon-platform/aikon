<script>
    import { getContext } from 'svelte';
    import {showMessage, withLoading} from "../utils.js";
    import { appLang, appName, csrfToken } from '../constants';

    const witness = getContext('witness');
    export let baseUrl = `${window.location.origin}${window.location.pathname}`;
    export let currentRegionId;
    export let activeTab;

    const allRegionsUrl = baseUrl.replace(/\/\d+\/?$/, "");

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
    {#if currentRegionId}
        {#if ["all", "page"].includes(activeTab) }
            <a href="{allRegionsUrl}" class="tag is-dark mr-3 is-rounded">All regions</a>
            <button on:click={deleteRegions} class="tag is-danger">
                {appLang === "en" ? "Delete regions extraction record" : "Supprimer l'extraction de régions"}
            </button>
        {:else if activeTab === "similarity"}
            <button on:click={deleteSimilarity} class="tag is-danger">
                {appLang === "en" ? "Delete all regions similarity" : "Supprimer toutes les similarités du document"}
            </button>
        {/if}
    {:else}
        {#if ["all", "page", "similarity"].includes(activeTab) }
            {#each witness.regions as regionId}
                <a href="{baseUrl}{regionId}" class="tag is-dark mr-3 is-rounded">Regions extraction #{regionId}</a>
            {/each}
            <!--TODO add NEW REGIONS BUTTON (to create empty region in order to launch new automatic extraction)-->
        {/if}
    {/if}
</div>

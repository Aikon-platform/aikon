<script>
    import { getContext } from 'svelte';
    import {showMessage, withLoading} from "../utils.js";
    import { appLang, csrfToken } from '../constants';

    const witness = getContext('witness');
    export let baseUrl = `${window.location.origin}${window.location.pathname}`;
    export let currentRegionId;

    async function deleteRegions() {
        const confirmed = await showMessage(
            appLang === "en" ? "Are you sure you want to delete this record?" : "Voulez-vous vraiment supprimer cet enregistrement?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );

        if (!confirmed) {
            return;
        }

        if (typeof currentRegionId !== 'number') {
            throw new Error('Invalid region ID');
        }
        const url = `${window.location.origin}/regions/${currentRegionId}/delete`;
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
</script>

<div>
    {#if currentRegionId}
        <button on:click={deleteRegions} class="tag is-danger">
            {appLang === "en" ? "Delete regions record" : "Supprimer l'intégralité des régions"}
        </button>
    {:else}
        {#each witness.regions as regionId}
            <a href="{baseUrl}{regionId}" class="tag is-dark mr-3 is-rounded">Regions #{regionId}</a>
        {/each}
    {/if}
</div>

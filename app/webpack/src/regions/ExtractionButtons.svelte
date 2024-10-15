<script>
    import { showMessage, withLoading } from '../utils.js';
    import { appLang, appName, modules, csrfToken } from '../constants';
    import { getContext } from 'svelte';
    const witness = getContext('witness');
    export let currentRegionId;
    export let baseUrl;

    async function manualRegions() {
        const wlo = `${window.location.origin}/${appName}`
        let url = `${wlo}/witness/${witness.id}/regions/add`;
        if (witness.regions.length === 1 || currentRegionId){
            const regionId = currentRegionId || witness.regions[0];
            url = `${wlo}/witness/${witness.id}/regions/${regionId}/add`;
        }

        // todo : allow "witness/<int:wid>/digitization/<int:did>/regions/add"
        const response = await withLoading(() => fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
        }));

        if (!response.ok) {
            await showMessage(`Failed to create regions: '${response.statusText}'`, "Error");
            throw new Error(`Failed to create regions: '${response.statusText}'`);
        }

        let res;
        try {
            res = await response.json();
        } catch (error) {
            await showMessage(`Failed to parse JSON response: '${error}'`, "Error");
            throw new Error(`Failed to parse JSON response: '${error}'`);
        }

        if (res.hasOwnProperty('mirador_url')) {
            window.open(res.mirador_url);
        }
        if (res.hasOwnProperty('regions_id')) {
            window.location.href = `${baseUrl.split('regions/')[0]}regions/${res.regions_id}`;
        }
    }
    async function automaticRegions() {
        const url = `${window.location.origin}/${appName}/witness/${witness.id}/regions/extract`;
        const response = await withLoading(() => fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
        }));

        // TODO allow to choose regions model and other parameters available in treatment form

        let res;
        if (!response.ok) {
            try {
                res = await response.json();
            } catch (error) {
                await showMessage(`Failed to parse JSON response: '${error}'`, "Error");
                throw new Error(`Failed to parse JSON response: '${error}'`);
            }

            await showMessage(`Failed to launch regions extraction: '${res.response}'`, "Error");
            throw new Error(`Failed to launch regions extraction: '${res.response}'`);
        }

        await showMessage(
            appLang === "en" ? `Regions extraction task has been triggered!` : `La tâche d'extraction des régions a été déclenchée!`,
            appLang === "en" ? "Success" : "Succès"
        );
        window.location.href = `${window.location.origin}/${appName}/treatment`;
    }
</script>

<!--TODO handle multiple digitization for a single witness-->

<div class="is-center buttons is-centered pt-5">
    <button class="button is-link" on:click={manualRegions}>
        {appLang === 'en' ? 'Manually annotate' : 'Annoter manuellement'}
    </button>
    <!--TODO make it work-->
    <!--    <button class="button is-link is-light" on:click={importRegionsFile}>-->
    <!--        {appLang === 'en' ? 'Import regions file' : 'Importer un fichier de région'}-->
    <!--    </button>-->
    {#if modules.includes("regions")}
        <!--TODO make this button disappear if a task is already triggered for this witness ?-->
        <button class="button is-link is-inverted" on:click={automaticRegions}>
            {appLang === 'en' ? 'Automatic region extraction' : 'Extraction automatique des régions'}
        </button>
    {/if}
</div>

<script>
    export let witness;
    export let appLang = "en";
    export let baseUrl = `${window.location.origin}${window.location.pathname}`;
    // const currentRegionId = parseInt(baseUrl.split('regions/')[1].replace("/", ""));
    export let currentRegionId;

    async function deleteRegions() {
        // todo add confirmation modal

        if (typeof currentRegionId !== 'number') {
            throw new Error('Invalid region ID');
        }
        const url = `${window.location.origin}/regions/${currentRegionId}/delete`;
        try {
            const response = await fetch(url, {
                method: "DELETE",
                headers: { "X-CSRFToken": CSRF_TOKEN },
            });
            if (response.status !== 204) {
                throw new Error(`Failed to delete regions: '${response.statusText}'`);
            }
            window.location.href = `${baseUrl.split('regions/')[0]}regions/`;
        } catch (error) {
            console.error(error);
        }
    }
</script>

<div class="is-right">
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

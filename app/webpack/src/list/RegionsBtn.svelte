<script>
    export let witness;
    export let baseUrl;
    export let appLang = "en";
    const currentRegionId = baseUrl.split('regions/')[1];

    async function deleteRegions() {
        // const regions = witness.regions.map(region => region.id);
        // const url = `${baseUrl}/witness/${witness.id}/regions/delete`;
        // fetch(url, {
        //     method: "POST",
        //     headers: { "X-CSRFToken": CSRF_TOKEN },
        //     body: JSON.stringify({ regions }),
        // }).then(response => {
        //     if (response.status !== 204) {
        //         throw new Error(`Failed to delete regions: '${response.statusText}'`);
        //     }
        //     window.location.reload();
        // });
    }
</script>

<div class="is-right">
    {#if currentRegionId}
        <button on:click={deleteRegions} class="tag is-danger">
            {appLang === "en" ? "Delete regions record" : "Supprimer l'intégralité des régions"}
        </button>
    {:else}
        {#each witness.regions as regionId}
            <a href="{baseUrl}{regionId}" class="tag is-dark mr-3 is-rounded">#{regionId}</a>
        {/each}
    {/if}
</div>

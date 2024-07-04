<script>
    export let appLang = 'en';
    export let modules = [];
    export let witness = {};

    const baseUrl = `${window.location.origin}`

    async function newRegions() {
        // todo : allow "witness/<int:wid>/digitization/<int:did>/regions/add" and "witness/<int:wid>/regions/<int:rid>/add"
        const response = await fetch(
            `${baseUrl}/witness/${witness.id}/regions/add`,
            {
                method: "POST",
                headers: { "X-CSRFToken": CSRF_TOKEN },
            });

        if (response.status !== 204) {
            throw new Error(`Failed to create regions: '${response.statusText}'`);
        }
        // const res = await response.json();
        response.json().then(data => {
            if (data.mirador_url){
                window.open(data.mirador_url);
            }
        });
    }
</script>

<!--TODO handle multiple digitization for a single witness-->

<div class="is-center buttons is-centered pt-5">
    <button class="button is-link" on:click={newRegions}>
        {appLang === 'en' ? 'Manually annotate' : 'Annoter manuellement'}
    </button>
    <button class="button is-link is-light">
        {appLang === 'en' ? 'Import regions file' : 'Importer un fichier de région'}
    </button>
    {#if modules.includes("regions")}
        <button class="button is-link is-inverted">
            {appLang === 'en' ? 'Automatic region extraction' : 'Extraction automatique des régions'}
        </button>
    {/if}
</div>

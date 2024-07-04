<script>
    export let appLang = 'en';
    export let modules = [];
</script>

<div class="is-center buttons is-centered pt-5">
    <button class="button is-link">
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

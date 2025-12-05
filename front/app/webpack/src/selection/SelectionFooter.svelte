<script>
    export let selectionStore;

    const { isSaved, selection } = selectionStore;
    import {appLang, appName} from '../constants';

    export let isRegion = selectionStore.type !== 'document';
</script>

<footer class="modal-card-foot is-center">
    <div class="buttons">
        <button class="button button-close is-link is-light" on:click={() => selectionStore.empty()}>
            {appLang === 'en' ? 'Clear selection' : 'Vider la sélection'}
        </button>
        {#if $isSaved && !isRegion}
            <a class="button is-link" href="/{appName}/treatment/add/?document_set={$selection.id}">
                <span>
                    <i class="fa-solid fa-gear"></i>
                    {appLang === 'en' ? 'Go to treatment' : 'Accéder au traitement'}
                </span>
            </a>
        {:else}
            <button class="button is-link" on:click={() => selectionStore.save()}>
                <span>
                    <i class="fa-solid fa-floppy-disk"></i>
                    {appLang === 'en' ? 'Save selection' : 'Sauvegarder la sélection'}
                </span>
            </button>
        {/if}
        {#if !isRegion}
            <a class="button is-link is-dark" href="/{appName}/document-set/{$selection.id}/json" target="_blank">
                <span>
                    <i class="fa-solid fa-file-export"></i> JSON
                </span>
            </a>
            <a class="button is-link is-dark" href="/{appName}/document-set/{$selection.id}/zip" target="_blank">
                <span>
                    <i class="fa-solid fa-file-zipper"></i> ZIP
                </span>
            </a>
        {/if}
    </div>
</footer>

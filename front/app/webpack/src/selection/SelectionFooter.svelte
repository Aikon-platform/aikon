<script>
    import { selectionStore } from "./selectionStore.js";
    const { isSaved, selection } = selectionStore;
    import {appLang, appName} from '../constants';

    export let isRegion = true;
</script>

<footer class="modal-card-foot is-center">
    <div class="buttons">
        <button class="button button-close is-link is-light" on:click={() => selectionStore.empty(isRegion)}>
            {appLang === 'en' ? 'Clear selection' : 'Vider la sélection'}
        </button>
        {#if $isSaved}
            <a class="button is-link" href="/{appName}/treatment/add/?document_set={$selection(isRegion).id}">
                <span>
                    <i class="fa-solid fa-gear"></i>
                    {appLang === 'en' ? 'Go to treatment' : 'Accéder au traitement'}
                </span>
            </a>
        {:else}
            <button class="button is-link" on:click={() => selectionStore.save(isRegion)}>
                <span>
                    <i class="fa-solid fa-floppy-disk"></i>
                    {appLang === 'en' ? 'Save selection' : 'Sauvegarder la sélection'}
                </span>
            </button>
        {/if}
        <a class="button is-link" href="/{appName}/document-set/{$selection(isRegion).id}/json" target="_blank">
            <span>
                <i class="fa-solid fa-file-export"></i>
                {appLang === 'en' ? 'JSON API' : 'API JSON'}
            </span>
        </a>
        <a class="button is-link" href="/{appName}/document-set/{$selection(isRegion).id}/zip" target="_blank">
            <span>
                <i class="fa-solid fa-file-zipper"></i>
                {appLang === 'en' ? 'Export as ZIP' : 'Exporter en ZIP'}
            </span>
        </a>
    </div>
</footer>

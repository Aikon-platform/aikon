<script>
    import { selectionStore } from "./selectionStore.js";
    import { appLang } from '../constants';

    export let isRegion = true;
</script>

<footer class="modal-card-foot is-center">
    <div class="buttons">
        <button class="button is-link is-light" on:click={() => selectionStore.empty(isRegion)}>
            {appLang === 'en' ? 'Clear selection' : 'Vider la sélection'}
        </button>
        <button class="button is-link" on:click={() => selectionStore.save()}>
            <i class="fa-solid fa-floppy-disk"></i>
            {appLang === 'en' ? 'Save selection' : 'Sauvegarder la sélection'}
        </button>
    </div>
</footer>

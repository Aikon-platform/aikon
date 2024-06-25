<script>
    import {createEventDispatcher} from "svelte";

    const dispatch = createEventDispatcher();
    function commitSelection(updateType="save") {
        dispatch('commitSelection', { updateType });
    }
    export let appLang = 'en';
</script>

<footer class="modal-card-foot is-center">
    <div class="buttons">
        <button class="button is-link is-light" on:click={() => commitSelection('clear')}>
            {appLang === 'en' ? 'Clear selection' : 'Vider la sélection'}
        </button>
        <button class="button is-link" on:click={() => commitSelection('save')}>
            <i class="fa-solid fa-floppy-disk"></i>
            {appLang === 'en' ? 'Save selection' : 'Sauvegarder la sélection'}
        </button>
    </div>
</footer>

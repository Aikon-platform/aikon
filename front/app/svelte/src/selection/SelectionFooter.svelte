<script>
    import {appLang, appName} from "../constants";

    let { selectionStore, _isRegion } = $props();
    // set a default
    let isRegion = $derived(
        _isRegion === undefined
            ? selectionStore?.type !== "documentSet"
            : _isRegion
    );

    const { isSaved, selection } = selectionStore;
</script>

<footer class="modal-card-foot is-center">
    <div class="buttons">
        <button class="button button-close is-link is-light" onclick={() => selectionStore.empty()}>
            {appLang === "en" ? "Clear selection" : "Vider la sélection"}
        </button>
        {#if $isSaved && !isRegion}
            <a class="button is-link" href="/{appName}/treatment/add/?document_set={$selection?.id}">
                <span>
                    <i class="fa-solid fa-gear"></i>
                    {appLang === "en" ? "Go to treatment" : "Accéder au traitement"}
                </span>
            </a>
            <a class="button is-link is-dark" href="/{appName}/document-set/{$selection?.id}" target="_blank">
                <span>
                    <i class="fa-solid fa-file-export"></i>
                    {appLang === 'en' ? 'Explore corpus' : 'Explorer le corpus'}
                </span>
            </a>
        {:else}
            <button class="button is-link" onclick={() => selectionStore.save()}>
                <span>
                    <i class="fa-solid fa-floppy-disk"></i>
                    {appLang === "en" ? "Save selection" : "Sauvegarder la sélection"}
                </span>
            </button>
        {/if}
        <!--TODO fix export before displaying again-->
        <!--{#if !isRegion}-->
        <!--    <a class="button is-link is-dark" href="/{appName}/document-set/{$selection?.id}/json" target="_blank">-->
        <!--        <span>-->
        <!--            <i class="fa-solid fa-file-export"/> JSON-->
        <!--        </span>-->
        <!--    </a>-->
        <!--    <a class="button is-link is-dark" href="/{appName}/document-set/{$selection?.id}/zip" target="_blank">-->
        <!--        <span>-->
        <!--            <i class="fa-solid fa-file-zipper"/> ZIP-->
        <!--        </span>-->
        <!--    </a>-->
        <!--{/if}-->
    </div>
</footer>

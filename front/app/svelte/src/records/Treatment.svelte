<script>
    import Item from "./Item.svelte";
    import {appLang, appName, regionsType} from "../constants.js";
    import {getSuccess, showMessage} from "../utils.js";

    export let item;
    export let recordsStore;

    $: finished = item.is_finished;
    $: task_status = item.status;

    async function cancelTreatment() {
        const confirmed = await showMessage(
            appLang === "en" ? "Are you sure you want to cancel treatment?" : "Êtes-vous sûr de vouloir annuler le traitement en cours ?",
            appLang === "en" ? "Confirm cancel" : "Confirmer l'annulation",
            true
        );

        if (!confirmed) {
            return; // User cancelled
        }

        const success = await getSuccess(`/${appName}/treatment/${item.id}/cancel`);
        if (success) {
            finished = true;
            task_status = "CANCELLED";
        } else {
            await showMessage(
                appLang === "en" ? "Failed to cancel treatment" : "Erreur lors de l'annulation du traitement",
                appLang === "en" ? "Error" : "Erreur"
            )
        }
    }
</script>

<Item {item} {recordsStore}>
    <div slot="buttons">
        {#if !finished && item.api_tracking_id}
            <button class="button is-small is-rounded is-danger is-outlined px-2 py-1 mr-2"
                    title="{appLang === 'en' ? 'Cancel treatment' : 'Annuler le traitement'}"
                    on:click={cancelTreatment}>
                <i class="fa-solid fa-ban"></i>
                <span>
                    {appLang === 'en' ? 'Cancel treatment' : 'Annuler le traitement'}
                </span>
            </button>
        {:else if finished && task_status === "ERROR"}
            <a href="add/{item.query_parameters}" class="button is-small is-rounded is-primary is-outlined px-2 py-1 mr-2"
               title='{appLang === "en" ? "Relaunch same treatment" : "Relancer le même traitement"}'>
                <i class="fa-solid fa-arrow-rotate-left"></i>
                <span>
                {appLang === 'en' ? 'Relaunch same treatment' : 'Relancer le même traitement'}
                </span>
            </a>
        {/if}

        {#if task_status === "SUCCESS"}
            <span class="tag is-success p-1 mb-1">{task_status}</span>
        {:else if task_status === ("ERROR" || "CANCELLED")}
            <span class="tag is-danger p-1 mb-1" title="{item.info || 'Unknown error'}">{task_status}</span>
        {:else}
            <span class="tag is-info p-1 mb-1">{task_status}</span>
        {/if}
    </div>

    <div slot="body" class="pt-2 grid">
        {#if item.hasOwnProperty('selection') && item.selection.hasOwnProperty('selected') && item.selection.selected}
            {#each Object.entries(item.selection.selected) as [modelName, selectedRecords]}
                {#each Object.entries(selectedRecords) as [id, meta]}
                    <div>
                        <span class="tag is-rounded is-accent">{modelName} #{id}</span>
                        {meta.title}
                    </div>
                {/each}
            {/each}
        {/if}
    </div>
</Item>

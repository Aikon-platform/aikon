<script>
    import { run } from 'svelte/legacy';

    import Item from "./Item.svelte";
    import {appLang, appName, regionsType} from "../constants.js";
    import {getSuccess, showMessage} from "../utils.svelte.js";

    let { item, recordsStore } = $props();

    let finished = $state(item.is_finished);
    let task_status = $state(item.status);

    const updateItemStatus = (_item) => {
        finished = _item.is_finished;
        task_status = _item.status;
    }

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

    async function relaunchTreatment(e) {
        if (item.task_type !== "import") return;
        e.preventDefault();
        if (await getSuccess(`/${appName}/treatment/${item.id}/relaunch`)) {
            finished = false;
            task_status = "IN PROGRESS";
        } else {
            await showMessage(
                appLang === "en" ? "Failed to relaunch treatment" : "Erreur lors de la relance du traitement",
                appLang === "en" ? "Error" : "Erreur"
            );
        }
    }
    /** reactively update `finished` and `task_status` when the props item` changes */
    run(() => {
        updateItemStatus(item);
    });
</script>

<Item {item} {recordsStore}>
    {#snippet buttons()}
        <div >
            {#if !finished && (item.api_tracking_id || item.task_type === "import")}
                {@const cancelTitle = appLang === 'en' ? 'Cancel treatment' : 'Annuler le traitement'}
                <button class="button is-small is-rounded is-danger is-outlined px-2 py-1 mr-2"
                        title={cancelTitle} onclick={cancelTreatment}>
                    <i class="fa-solid fa-ban"></i>
                    <span>{cancelTitle}</span>
                </button>
            {:else if finished && task_status === "ERROR"}
                {@const relaunchTitle = appLang === 'en' ? "Relaunch same treatment" : "Relancer le même traitement"}
                <a href="add/{item.query_parameters}" onclick={relaunchTreatment} class="button is-small is-rounded is-primary is-outlined px-2 py-1 mr-2" title={relaunchTitle}>
                    <i class="fa-solid fa-arrow-rotate-left"></i>
                    <span>{relaunchTitle}</span>
                </a>
            {/if}

            {#if task_status === "SUCCESS"}
                <span class="tag is-success p-1 mb-1">{task_status}</span>
            {:else if ["ERROR", "CANCELLED"].includes(task_status)}
                <span class="tag is-danger p-1 mb-1" title="{item.info || 'Unknown error'}">{task_status}</span>
            {:else}
                <span class="tag is-info p-1 mb-1">{task_status}</span>
            {/if}
        </div>
    {/snippet}

    {#snippet body()}
        <div  class="pt-2 grid">
            {#if item.hasOwnProperty("selection") && item.selection.hasOwnProperty("selected") && item.selection.selected}
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
    {/snippet}
</Item>

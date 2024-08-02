<script>
    import Item from "./Item.svelte";
    import {appLang} from "../constants.js";
    import {cancelTreatment} from "../utils.js";
    export let item;
</script>

<Item {item}>
    <div slot="buttons">
        {#if !item.is_finished && item.api_tracking_id}
            <button class="button is-small is-rounded is-danger is-outlined px-2 py-1 mr-2"
                    title="{appLang === 'en' ? 'Cancel treatment' : 'Annuler le traitement'}"
                    on:click={() => cancelTreatment(item.id)}>
                <i class="fa-solid fa-ban"></i>
                <span>
            {appLang === 'en' ? 'Cancel treatment' : 'Annuler le traitement'}
        </span>
            </button>
        {:else if item.is_finished && item.status === "ERROR"}
            <a href="add/{item.query_parameters}" class="button is-small is-rounded is-primary is-outlined px-2 py-1 mr-2"
               title='{appLang === "en" ? "Relaunch same treatment" : "Relancer le même traitement"}'>
                <i class="fa-solid fa-arrow-rotate-left"></i>
                <span>
                {appLang === 'en' ? 'Relaunch same treatment' : 'Relancer le même traitement'}
                </span>
            </a>
        {/if}

        {#if item.status === "SUCCESS"}
            <span class="tag is-success p-1 mb-1">{item.status}</span>
        {:else if item.status === ("ERROR" || "CANCELLED")}
            <span class="tag is-danger p-1 mb-1">{item.status}</span>
        {:else}
            <span class="tag is-info p-1 mb-1">{item.status}</span>
        {/if}
    </div>

    <div slot="body" class="pt-2 grid">
        {#each Object.entries(item.selection.selected) as [modelName, selectedRecords]}
            {#each Object.entries(selectedRecords) as [id, meta]}
                <div>
                    <span class="tag is-rounded is-accent">{modelName} #{id}</span>
                    {meta.title}
                </div>
            {/each}
        {/each}
    </div>
</Item>

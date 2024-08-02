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

    <div slot="body" class="grid metadata pt-2">
        {#each Object.entries(item.metadata) as [field, value]}
            <div class="datum is-middle columns">
                <div class="column is-4 is-bold">{field}</div>
                <div class="column is-8 {value === '-' ? 'faded' : ''}">{@html value}</div>
            </div>
        {/each}
    </div>
</Item>

<style>
    .metadata {
        color: var(--bulma-text-strong);
    }
    .metadata .datum:not(:nth-last-child(-n+2)) {
        border-bottom: 1px solid var(--bulma-border);
    }
    .columns {
        margin-bottom: 0.5rem;
    }
</style>

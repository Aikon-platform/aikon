<script>
    import { refToIIIF, cancelTreatment } from "../utils.js";
    import { selectionStore } from '../selection/selectionStore.js';
    const { isSelected } = selectionStore;
    import { appLang } from '../constants';
    export let item;
    $: itemSelected = $isSelected(item);

    // TODO add delete button if USER is the creator of the record
</script>

<div class="item">
    <div class="card mb-3">
        <div class="card-content">
            <div class="media">
                {#if item.class === "Witness"}
                <div class="media-left">
                    <figure class="card image is-96x96">
                        <img src="{refToIIIF(item.img, 'full', '250,')}" alt="Record illustration"/>
                    </figure>
                </div>
                {/if}
                <div class="media-content">
                    <a href="{item.url}" class="title is-4 hoverable pt-2">
                        <span class="tag px-2 py-1 mb-1 is-dark is-rounded">{item.type} #{item.id}</span>
                        {item.title}
                        {#if item.is_public}
                            <span class="pl-3 icon-text is-size-7 is-center has-text-weight-normal">
                                <span class="icon has-text-success"><i class="fas fa-check-circle"></i></span>
                                <span style="margin-left: -0.5rem">Public</span>
                            </span>
                        {/if}
                    </a>

                    <p class="subtitle is-6 mb-0 ml-2 pt-2">
                        {item.user}
                        {#if item.updated_at}
                        <span class="tag p-1 mb-1">{item.updated_at}</span>
                        {/if}
                    </p>

                    {#if item.buttons}
                        <p class="subtitle is-6 mb-0 ml-2 pt-2">
                            {#if item.hasOwnProperty('iiif')}
                                {#each item.iiif as iiif}
                                    <span class="tag logo mt-1">{@html iiif}</span>
                                {/each}
                            {/if}
                            {#if item.buttons.includes("regions")}
                                <a href="{item.url}regions/" class="button is-small is-rounded is-link px-2 py-1"
                                   title="{appLang === 'en' ? 'View image regions' : 'Afficher les régions d\'images'}">
                                    <span class="iconify" data-icon="entypo:documents"/>
                                    <span class="ml-2">
                                        {appLang === 'en' ? 'Show regions' : 'Afficher les régions'}
                                    </span>
                                </a>
                            {/if}
                        </p>
                    {/if}
                </div>
                <div class="media-right">
                    {#if item.class === "Treatment"}
                        {#if !item.is_finished && item.api_tracking_id}
                            <button class="button is-small is-rounded is-danger is-outlined px-2 py-1 mr-2"
                                title="{appLang === 'en' ? 'Cancel treatment' : 'Annuler le traitement'}"
                                on:click={() => cancelTreatment(item.id)}>
                                <i class="fa-solid fa-ban"></i>
                                <span>
                                    {appLang === 'en' ? 'Cancel treatment' : 'Annuler le traitement'}
                                </span>
                            </button>
                        {/if}
                        {#if item.status === "SUCCESS"}
                        <span class="tag is-success p-1 mb-1">{item.status}</span>
                        {:else if item.status === ("ERROR" || "CANCELLED")}
                        <span class="tag is-danger p-1 mb-1">{item.status}</span>
                        {:else}
                        <span class="tag is-info p-1 mb-1">{item.status}</span>
                        {/if}
                    {:else}
                    <button class="button" class:is-inverted={itemSelected} on:click={() => selectionStore.toggle(item)}>
                        {#if appLang === 'en'}
                            {itemSelected ? 'Remove from' : 'Add to'} selection
                        {:else}
                            {itemSelected ? 'Retirer de la' : 'Ajouter à la'} sélection
                        {/if}
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                            {#if itemSelected}
                                <path fill="currentColor" d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"/>
                            {:else}
                                <path fill="currentColor" d="M0 48C0 21.5 21.5 0 48 0l0 48V441.4l130.1-92.9c8.3-6 19.6-6 27.9 0L336 441.4V48H48V0H336c26.5 0 48 21.5 48 48V488c0 9-5 17.2-13 21.3s-17.6 3.4-24.9-1.8L192 397.5 37.9 507.5c-7.3 5.2-16.9 5.9-24.9 1.8S0 497 0 488V48z"/>
                            {/if}
                        </svg>
                    </button>
                    {/if}
                </div>
            </div>

            <div class="content fixed-grid px-5">
                <div class="grid metadata pt-2">
                    {#each Object.entries(item.metadata) as [field, value]}
                        <div class="datum is-middle columns">
                            <div class="column is-3 is-bold">{field}</div>
                            <div class="column is-8 {value === '-' ? 'faded' : ''}">{value}</div>
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .card.image {
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .hoverable:hover {
        cursor: pointer;
        text-decoration: underline;
    }
    svg {
        padding-left: 10px !important;
        height: 1em;
        overflow: visible;
        vertical-align: -.125em;
    }
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

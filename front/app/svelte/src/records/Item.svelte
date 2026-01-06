<script>
    import { fade } from 'svelte/transition';
    import {deleteRecord, refToIIIF, showMessage} from "../utils.js";
    import { appLang, userId, isSuperuser } from '../constants';

    export let recordsStore;

    export let item;
    const hasViewUrl = item.hasOwnProperty("view_url") && item.view_url !== "";
    const hasEditUrl = item.hasOwnProperty("edit_url") && item.edit_url !== "";

    async function deleteItem() {
        // TODO add delete button if USER is the creator of the record OR super admin
        const confirmed = await showMessage(
            appLang === "en" ? "Are you sure you want to delete this record?" : "Voulez-vous vraiment supprimer cet enregistrement ?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );
        if (!confirmed) {
            return; // User cancelled the deletion
        }

        const success = await deleteRecord(item.id, item.class);
        if (success) {
            recordsStore.remove(item.id);
        } else {
            await showMessage(
                appLang === "en" ? "Failed to delete record" : "Erreur lors de la suppression de l'enregistrement",
                appLang === "en" ? "Error" : "Erreur"
            );
        }
    }
</script>

<div class="item" transition:fade={{ duration: 500 }}>
    <div class="card mb-5">
        <div class="card-content">
            <div class="media">
                {#if item.hasOwnProperty('img')}
                    <div class="media-left">
                        <figure class="card image is-96x96">
                            <img src="{refToIIIF(item.img, 'full', '250,')}" alt="Record illustration"/>
                        </figure>
                    </div>
                {/if}
                <div class="media-content">
                    <a href={hasViewUrl ? item.view_url : null} class="title is-4 {hasViewUrl ? 'hoverable' : ''} pt-2">
                        <span class="tag px-2 py-1 mb-1 mr-1 is-dark is-rounded">{item.type} #{item.id}</span>
                        {item.title}
                    </a>
                    {#if item.hasOwnProperty("is_public") && item.is_public}
                        <span class="pl-3 pt-1 icon-text is-size-7 is-center has-text-weight-normal">
                            <span class="icon has-text-success"><i class="fas fa-check-circle"></i></span>
                            <span style="margin-left: -0.5rem">Public</span>
                        </span>
                    {/if}

                    <p class="subtitle is-6 mb-0 ml-2 pt-2">
                        {#if item.user}
                            {item.user}
                        {/if}
                        {#if item.updated_at}
                            <span class="tag p-1 mb-1">{item.updated_at}</span>
                        {/if}
                    </p>

                    <p class="subtitle is-6 mb-0 ml-2 pt-2 is-middle">
                        {#if hasEditUrl}
                            <a href={hasEditUrl ? item.edit_url : null} class="edit-btn button is-small is-rounded is-link px-2"
                               title='{appLang === "en" ? "Edit" : "Éditer"}'>
                                <span class="iconify" data-icon="entypo:edit"/>
                                <span class="ml-2">
                                    {appLang === 'en' ? 'Edit' : 'Éditer'}
                                </span>
                            </a>
                        {/if}
                        {#if item.hasOwnProperty("buttons") && Object.keys(item.buttons).length !== 0}
                            {#if item.hasOwnProperty('iiif')}
                                {#each item.iiif as iiif}
                                    <span class="tag logo mt-1">{@html iiif}</span>
                                {/each}
                            {/if}
                        {/if}
                    </p>
                </div>
                <div class="media-right">
                    <slot name="buttons"/>
                </div>
                {#if item.class === 'Treatment' || item.class === 'DocumentSet'}
                    {#if item.user_id === parseInt(userId) || isSuperuser}
                        <button class="delete is-medium" title="{appLang === 'en' ? 'Delete' : 'Supprimer'}" on:click={deleteItem}/>
                    {/if}
                {/if}
            </div>

            <div class="content fixed-grid px-5">
                <slot name="body"/>
            </div>
        </div>
    </div>
</div>

<style>
    .edit-btn {
        padding-bottom: .15rem !important;
        padding-top: .15rem !important;
    }
    .card.image {
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    a:not(.hoverable) {
        cursor: default !important;
    }
</style>

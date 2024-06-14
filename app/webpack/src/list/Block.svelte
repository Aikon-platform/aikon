<script>
    import {refToIIIF} from "../utils.js";
    // import {useToggleSelection} from './documentSet.js';
    import {createEventDispatcher} from "svelte";

    export let block;
    export let appLang;
    export let isSelected = false;

    const dispatch = createEventDispatcher();

    function toggleSelection(block) {
        dispatch('toggleSelection', { block });
        isSelected = !isSelected
    }
</script>

<style>
    .card.image {
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    svg {
        padding-left: 10px !important;
        height: 1em;
        overflow: visible;
        vertical-align: -.125em;
    }

    .hoverable:hover {
        cursor: pointer;
        text-decoration: underline;
    }
</style>

{#if block.hasOwnProperty('metadata')}
    <div class="block">
        <div id="block-{block.id}" class="card">
            <div class="card-content">
                <div class="media">
                    <div class="media-left">
                        <figure class="card image is-96x96">
                            <img src="{refToIIIF(block.img, 'full', '250,')}" alt="Record illustration"/>
                        </figure>
                    </div>
                    <div class="media-content">
                        <a href="/{block.class.toLowerCase()}/{block.id}" class="title is-4 hoverable pt-2">
                            <span class="tag px-2 py-1 mb-1 is-dark is-rounded">{block.type} #{block.id}</span>
                            {block.title}
                            {#if block.is_public}
                                <span class="pl-3 icon-text is-size-7 is-center has-text-weight-normal">
                                    <span class="icon has-text-success"><i class="fas fa-check-circle"></i></span>
                                    <span style="margin-left: -0.5rem">Public</span>
                                </span>
                            {/if}
                        </a>

                        <p class="subtitle is-6 mb-0 ml-2 pt-2">
                            {block.user}
                            <span class="tag p-1 mb-1">{block.updated_at}</span>
                        </p>
                    </div>
                    <div class="media-right">
                            <button class="button {isSelected ? 'is-inverted' : ''}" id="set-{block.id}" on:click={() => toggleSelection(block)}>
                                {#if appLang === 'en'}
                                    {isSelected ? 'Remove from' : 'Add to'} set
                                {:else}
                                    {isSelected ? 'Retirer de' : 'Ajouter à la'} sélection
                                {/if}
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                                    {#if isSelected}
                                        <path fill="currentColor" d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"/>
                                    {:else}
                                        <path fill="currentColor" d="M0 48C0 21.5 21.5 0 48 0l0 48V441.4l130.1-92.9c8.3-6 19.6-6 27.9 0L336 441.4V48H48V0H336c26.5 0 48 21.5 48 48V488c0 9-5 17.2-13 21.3s-17.6 3.4-24.9-1.8L192 397.5 37.9 507.5c-7.3 5.2-16.9 5.9-24.9 1.8S0 497 0 488V48z"/>
                                    {/if}
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div class="content">
                        <table class="table pl-2 is-fullwidth">
                            <tbody>
                            {#each Object.entries(block.metadata) as [field, value]}
                                <tr>
                                    <th class="is-narrow is-3">{field}</th>
                                    <td>{value}</td>
                                </tr>
                            {/each}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
{:else}
    <div class="region block card">
        <figure id="region-{block.id}" class="image is-96x96">
            <img src="{refToIIIF(block.img, 'full', '250,')}" alt="Extracted region"/>
        </figure>
        <button class="button" id="set-{block.id}" on:click={() => toggleSelection(block)}>
            {#if isSelected}
                <i class="fa-solid fa-bookmark"></i> {appLang === 'en' ? 'Remove from set' : 'Retirer de la sélection'}
            {:else}
                <i class="fa-regular fa-bookmark"></i> {appLang === 'en' ? 'Add to set' : 'Ajouter à la sélection'}
            {/if}
        </button>
    </div>
{/if}

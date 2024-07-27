<script>
    import { onMount } from 'svelte';
    import Record from "./Record.svelte";
    import { recordsStore } from "./recordStore.js";
    const { pageRecords, resultPage } = recordsStore;
    import { selectionStore } from "../selection/selectionStore.js";
    const { selected, nbSelected } = selectionStore;
    import SelectionBtn from "../selection/SelectionBtn.svelte";
    import SelectionFooter from "../selection/SelectionFooter.svelte";
    import {appLang, regionsType} from '../constants';
    import {refToIIIF} from "../utils.js";
    import SelectionModal from "../selection/SelectionModal.svelte";
    import RecordSearch from "./RecordSearch.svelte";
    // export let records = [];

    $: selectedRecords = $selected(false);
    $: selectionLength = $nbSelected(false);

</script>

<SelectionBtn {selectionLength}/>

<RecordSearch/>

{#await resultPage}
    <div class="faded is-center">
        {appLang === 'en' ? 'Retrieving records...' : 'Récupération des enregistrements...'}
    </div>
{:then _}
    {#if $pageRecords.length !== 0}
        <div>
            {#each $pageRecords as item (item.id)}
                <Record {item}/>
            {:else}
                <p>{appLang === 'en' ? 'No records found' : 'Aucun enregistrement trouvé'}</p>
            {/each}
        </div>
    {/if}
{:catch error}
    <div class="faded is-center">
        {appLang === 'en' ? 'Error when retrieving records: ' : 'Erreur lors de la récupération des enregistrements : '}
        {error}
    </div>
{/await}

<SelectionModal {selectionLength}>
    {#each selectedRecords as [type, selectedItems]}
        <h3>{type}</h3>
        <table class="table pl-2 is-fullwidth">
            <tbody>
            {#each Object.entries(selectedItems) as [id, meta]}
                <tr>
                    <th class="is-narrow is-3">
                        <span class="tag px-2 py-1 mb-1 is-dark is-rounded">#{id}</span>
                    </th>
                    <td>
                        <a href="{meta.url}" target="_blank">{meta.title}</a>
                    </td>
                    <td class="is-narrow">
                        <button class="delete" aria-label="close"
                                on:click={() => selectionStore.remove(id, type)}/>
                    </td>
                </tr>
            {:else}
                <tr>
                    <td>
                        {appLang === 'en' ? 'No documents in selection' : 'Aucun document sélectionné'}
                    </td>
                </tr>
            {/each}
            </tbody>
        </table>
    {:else}
        <tr>
            <td>
                {appLang === 'en' ? 'No documents in selection' : 'Aucun document sélectionné'}
            </td>
        </tr>
    {/each}
</SelectionModal>

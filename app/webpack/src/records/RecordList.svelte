<script>
    import Record from "./Record.svelte";
    import { selectionStore } from "../selection/selectionStore.js";
    const { selected, nbSelected } = selectionStore;
    import SelectionBtn from "../selection/SelectionBtn.svelte";
    import { appLang } from '../constants';
    import SelectionModal from "../selection/SelectionModal.svelte";
    import RecordSearch from "./RecordSearch.svelte";
    import Pagination from "../Pagination.svelte";
    import { setContext } from "svelte";

    export let modelName = '';
    setContext('modelName', modelName);

    import { createRecordsStore } from "./recordStore.js";
    const recordsStore = createRecordsStore(modelName);
    const { pageRecords, resultPage, resultNumber } = recordsStore;

    $: selectedRecords = $selected(false);
    $: selectionLength = $nbSelected(false);


    export let searchFields = [];
    // TODO make result count appear + filter name
</script>

<SelectionBtn {selectionLength}/>

<RecordSearch {recordsStore} {searchFields}/>

{#await resultPage}
    <div class="faded is-center">
        {appLang === 'en' ? 'Retrieving records...' : 'Récupération des enregistrements...'}
    </div>
{:then _}
    {#if $pageRecords.length !== 0}
        <Pagination store={recordsStore} nbOfItems={$resultNumber}/>
        <div>
            {#each $pageRecords as item (item.id)}
                <Record {item}/>
            {:else}
                <p>{appLang === 'en' ? 'No records found' : 'Aucun enregistrement trouvé'}</p>
            {/each}
        </div>
        <Pagination store={recordsStore} nbOfItems={$resultNumber}/>
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

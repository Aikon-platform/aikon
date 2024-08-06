<script>
    import Record from "./Record.svelte";
    import { selectionStore } from "../selection/selectionStore.js";
    const { selected, nbSelected } = selectionStore;
    import SelectionBtn from "../selection/SelectionBtn.svelte";
    import { appLang, appName, webappName } from '../constants';
    import SelectionModal from "../selection/SelectionModal.svelte";
    import RecordSearch from "./RecordSearch.svelte";
    import Pagination from "../Pagination.svelte";
    import Modal from "../Modal.svelte";
    // import Loading from '../Loading.svelte';
    // import { loading } from "../utils.js";

    import { setContext } from "svelte";

    export let modelName = '';
    setContext('modelName', modelName);

    export let modelTitle = '';
    setContext('modelTitle', modelTitle);

    import { createRecordsStore } from "./recordStore.js";
    import Set from "./Set.svelte";
    import Treatment from "./Treatment.svelte";
    const recordsStore = createRecordsStore(modelName);
    const { pageRecords, resultPage, resultNumber } = recordsStore;

    $: selectedRecords = $selected(false);
    $: selectionLength = $nbSelected(false);

    export let searchFields = [];
    // TODO make result count appear + filter name

    const addUrl = modelTitle.includes('Treatment') ? `/${appName}-admin/${modelName}/add/` : `/${appName}/${webappName}/${modelName}/add/`
</script>

<!--<Loading visible={$loading}/>-->

<Modal/>

<SelectionBtn {selectionLength}/>

<RecordSearch {recordsStore} {searchFields}/>

{#if !modelTitle.includes('set')}
    <span class="is-right">
        <a href="{addUrl}" class="button is-rounded is-primary mb-4"
           title='{appLang === "en" ? "Add" : "Ajouter"}'>
            <i class="fa-solid fa-plus"></i>
            <span>{appLang === 'en' ? "Add" : "Ajouter"}</span>
        </a>
    </span>
{/if}

{#await resultPage}
    <div class="faded is-center">
        {appLang === 'en' ? 'Retrieving records...' : 'Récupération des enregistrements...'}
    </div>
{:then _}
    {#if $pageRecords.length !== 0}
        <Pagination store={recordsStore} nbOfItems={$resultNumber} pageLength={$pageRecords.length}/>
        <div>
            {#each $pageRecords as item (item.id)}
                {#if item.class.includes('Treatment')}
                    <Treatment {item} {recordsStore}/>
                {:else if item.class.includes('Set')}
                    <Set {item}/>
                {:else}
                    <Record {item}/>
                {/if}
            {:else}
                <p>{appLang === 'en' ? 'No records found' : 'Aucun enregistrement trouvé'}</p>
            {/each}
        </div>
        <Pagination store={recordsStore} nbOfItems={$resultNumber} pageLength={$pageRecords.length}/>
    {/if}
{:catch error}
    <div class="faded is-center">
        {appLang === 'en' ? 'Error when retrieving records: ' : 'Erreur lors de la récupération des enregistrements : '}
        {error}
    </div>
{/await}

<SelectionModal {selectionLength}>
    {#each selectedRecords as [type, selectedItems]}
        {#if Object.values(selectedItems).length > 0}
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
                    <!--{:else}-->
                    <!--    <tr>-->
                    <!--        <td>-->
                    <!--            {appLang === 'en' ? 'No documents in selection' : 'Aucun document sélectionné'}-->
                    <!--        </td>-->
                    <!--    </tr>-->
                {/each}
                </tbody>
            </table>
        {/if}
    {:else}
        <tr>
            <td>
                {appLang === 'en' ? 'No documents in selection' : 'Aucun document sélectionné'}
            </td>
        </tr>
    {/each}
</SelectionModal>

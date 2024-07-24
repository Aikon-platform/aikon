<script>
    import Record from "./Record.svelte";
    import { selectionStore } from "../selection/selectionStore.js";
    const { selected, nbSelected } = selectionStore;
    import SelectionBtn from "../selection/SelectionBtn.svelte";
    import SelectionFooter from "../selection/SelectionFooter.svelte";
    import {appLang, regionsType} from '../constants';
    import {refToIIIF} from "../utils.js";
    import SelectionModal from "../selection/SelectionModal.svelte";
    export let records = [];

    $: selectedRecords = $selected(false);
    $: selectionLength = $nbSelected(false);
</script>

<SelectionBtn {selectionLength}/>

{#if records.length !== 0}
    <div>
        {#each records as item (item.id)}
            <Record {item}/>
        {:else}
            <p>{appLang === 'en' ? 'No records found' : 'Aucun document trouvé'}</p>
        {/each}
    </div>
{/if}

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

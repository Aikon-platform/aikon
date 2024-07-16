<script>
    import Record from "./Record.svelte";
    import { selectionStore } from "../selection/selectionStore.js";
    const { selected, nbSelected } = selectionStore;
    import SelectionBtn from "../selection/SelectionBtn.svelte";
    import SelectionFooter from "../selection/SelectionFooter.svelte";
    import { appLang } from '../constants';
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

<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"></div>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <i class="fa-solid fa-book-bookmark"></i>
                {appLang === 'en' ? 'Selected documents' : 'Documents sélectionnés'}
                ({selectionLength})
            </div>
            <button class="delete media-left" aria-label="close"></button>
        </div>
        <section class="modal-card-body">
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
        </section>
        <SelectionFooter isRegion={false}/>
    </div>
</div>

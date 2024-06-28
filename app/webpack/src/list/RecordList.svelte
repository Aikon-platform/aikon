<script>
    import Record from "./Record.svelte";
    import {saveSelection, emptySelection, addToSelection, removeFromSelection} from "./selection.js";
    import SelectionBtn from "./SelectionBtn.svelte";
    import SelectionFooter from "./SelectionFooter.svelte";
    export const regionsType = "Regions";
    export let records = [];

    export let appLang = 'en';

    let selection = JSON.parse(localStorage.getItem("documentSet")) ?? {};
    const filterSelection = (selection) => Object.entries(selection).filter(([key, _]) => key !== regionsType);
    $: selectionLength = filterSelection(selection).reduce((count, [_, selectedBlocks]) => count + Object.keys(selectedBlocks).length, 0);
    $: isBlockSelected = (block) => selection[block.type]?.hasOwnProperty(block.id);

    function handleCommitSelection(event) {
        const { updateType } = event.detail;

        if (updateType === 'clear') {
            selection = emptySelection(selection, Object.keys(selection).filter(key => key !== regionsType));
        } else if (updateType === 'save') {
            selection = saveSelection(selection);
        }
    }

    function removeRecord(blockId, blockType) {
        selection = removeFromSelection(selection, blockId, blockType);
    }

    function addRecord(block) {
        selection = addToSelection(selection, block);
    }

    function handleToggleSelection(event) {
        const { block } = event.detail;

        if (!isBlockSelected(block)) {
            addRecord(block);
        } else {
            removeRecord(block.id, block.type);
        }
    }

</script>

<SelectionBtn {selectionLength} {appLang} />

{#if records.length !== 0}
    <div>
        {#each records as block (block.id)}
            <Record {block} appLang={appLang} isSelected={isBlockSelected(block)} on:toggleSelection={handleToggleSelection} />
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
            {#each filterSelection(selection) as [type, selectedBlocks]}
                <h3>{type}</h3>
                <table class="table pl-2 is-fullwidth">
                    <tbody>
                    {#each Object.entries(selectedBlocks) as [id, meta]}
                        <tr>
                            <th class="is-narrow is-3">
                                <span class="tag px-2 py-1 mb-1 is-dark is-rounded">#{id}</span>
                            </th>
                            <td>
                                <a href="{meta.url}" target="_blank">{meta.title}</a>
                            </td>
                            <td class="is-narrow">
                                <button class="delete" aria-label="close" on:click={() => removeRecord(id, type)}></button>
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
        <SelectionFooter {appLang} on:commitSelection={handleCommitSelection}/>
    </div>
</div>

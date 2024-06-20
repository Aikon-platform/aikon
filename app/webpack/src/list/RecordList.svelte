<script>
    import Record from "./Record.svelte";
    import {saveSelection, emptySelection, addToSelection, removeFromSelection} from "./selection.js";

    let addAnimation = false;
    let removeAnimation = false;
    export const regionsType = "Regions";
    export let records = [];

    export let appLang = 'en';

    let selection = JSON.parse(localStorage.getItem("documentSet")) ?? {};
    const selectionLength = Object.entries(selection)
        .filter(([key, _]) => key !== regionsType)
        .reduce((count, [_, selectedBlocks]) => count + Object.keys(selectedBlocks).length, 0);
    $: isBlockSelected = (block) => selection[block.type]?.hasOwnProperty(block.id);

    function commitSelection() {
        saveSelection(selection);
    }

    function clearSelection() {
        selection = emptySelection()
    }

    function removeRecord(blockId, blockType) {
        selection = removeFromSelection(selection, blockId, blockType);
        removeAnimation = true;
        setTimeout(() => removeAnimation = false, 300);
    }

    function addRecord(block) {
        selection = addToSelection(selection, block);
        addAnimation = true;
        setTimeout(() => addAnimation = false, 300);
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

<div class="set-container">
    <button id="set-btn"
            class="button px-5 py-4 is-link js-modal-trigger"
            data-target="selection-modal"
            class:add-animation={addAnimation}
            class:remove-animation={removeAnimation}>
        <span>
            <i class="fa-solid fa-book-bookmark"></i>
            {appLang === 'en' ? 'Selection' : 'Sélection'}
            (<span id="selection-count">{selectionLength}</span>)
        </span>

    </button>
</div>

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
                (<span id="selection-count">{selectionLength}</span>)
            </div>
            <button class="delete media-left" aria-label="close"></button>
        </div>
        <section class="modal-card-body">
            {#each Object.entries(selection) as [type, selectedBlocks]}
                {#if type !== regionsType}
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
                                    <button class="delete" aria-label="close" on:click={() => removeFromSelection(id, type)}></button>
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
                {/if}
            {/each}
        </section>
        <footer class="modal-card-foot is-centered">
            <div class="buttons">
                <button class="button is-link is-light" on:click={clearSelection}>
                    {appLang === 'en' ? 'Clear selection' : 'Vider la sélection'}
                </button>
                <button class="button is-link" on:click={commitSelection}>
                    <i class="fa-solid fa-floppy-disk"></i>
                    {appLang === 'en' ? 'Save selection' : 'Sauvegarder la sélection'}
                </button>
            </div>
        </footer>
    </div>
</div>

<script>
    import Region from './Region.svelte';
    import {saveSelection, emptySelection, addToSelection, removeFromSelection} from "./selection.js";
    import SelectionBtn from "./SelectionBtn.svelte";
    import SelectionFooter from "./SelectionFooter.svelte";

    let addAnimation = false;
    let removeAnimation = false;
    export const regionsType = "Regions"
    export let regions = [];

    export let appLang = 'en';

    let selection = JSON.parse(localStorage.getItem("documentSet")) ?? {};
    $: selectionLength = selection.hasOwnProperty(regionsType) ? Object.keys(selection[regionsType]).length : 0;
    $: isBlockSelected = (block) => selection[regionsType]?.hasOwnProperty(block.id);

    function handleCommitSelection(event) {
        const { updateType } = event.detail;
        if (updateType === 'clear') {
            selection = emptySelection(selection, [regionsType]);
        } else if (updateType === 'save') {
            selection = saveSelection(selection);
        }
    }

    function removeRegion(blockId) {
        selection = removeFromSelection(selection, blockId, regionsType);
        removeAnimation = true;
        setTimeout(() => removeAnimation = false, 300);
    }

    function addRegion(block) {
        selection = addToSelection(selection, block);
        addAnimation = true;
        setTimeout(() => addAnimation = false, 300);
    }

    function handleToggleSelection(event) {
        const { block } = event.detail;
        if (!isBlockSelected(block)) {
            addRegion(block);
        } else {
            removeRegion(block.id);
        }
    }

</script>

<SelectionBtn {addAnimation} {removeAnimation} {selectionLength} {appLang} />

{#if regions.length !== 0}
    <div class="fixed-grid has-auto-count">
        <div class="grid is-gap-2">
            {#each regions as block (block.id)}
                <Region {block} appLang={appLang} isSelected={isBlockSelected(block)} on:toggleSelection={handleToggleSelection} />
            {:else}
                <!--Create manual annotation btn-->
            {/each}
        </div>
    </div>
{/if}

<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"></div>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <i class="fa-solid fa-book-bookmark"></i>
                {appLang === 'en' ? 'Selected regions' : 'Regions sélectionnées'}
                (<span id="selection-count">{selectionLength}</span>)
            </div>
            <button class="delete media-left" aria-label="close"></button>
        </div>
        <section class="modal-card-body">
            <table class="table pl-2 is-fullwidth">
                <tbody>
                {#if selection.hasOwnProperty(regionsType) && Object.keys(selection[regionsType]).length > 0}
                    {#each Object.entries(selection[regionsType]) as [id, meta]}
                        <tr>
                            <th class="is-narrow is-3">
                                <span class="tag px-2 py-1 mb-1 is-dark is-rounded">#{id}</span>
                            </th>
                            <td>
                                <a href="{meta.url}" target="_blank">{meta.title}</a>
                            </td>
                            <td class="is-narrow">
                                <button class="delete" aria-label="close" on:click={() => removeRegion(id)}></button>
                            </td>
                        </tr>
                    {/each}
                {:else}
                    <tr>
                        <td>
                            {appLang === 'en' ? 'No regions in selection' : 'Aucune région sélectionnée'}
                        </td>
                    </tr>
                {/if}
                </tbody>
            </table>
        </section>
        <SelectionFooter {appLang} on:commitSelection={handleCommitSelection}/>
    </div>
</div>

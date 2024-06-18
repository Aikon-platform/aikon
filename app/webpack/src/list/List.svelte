<script>
    import Block from './Block.svelte';

    // todo handle ordering (pass all blocks to view?)

    export let blocks = [];
    export let appLang = 'en';
    let addAnimation = false;
    let removeAnimation = false;

    let selection = JSON.parse(localStorage.getItem('documentSet')) ?? {};
    $: selectionLength = Object.keys(selection).length;

    $: isBlockSelected = (block) => selection.hasOwnProperty(block.id);

    function saveSelection() {
        console.log(selection);
        // api call to save set in database
        // receive id of saved
    }

    function clearSelection() {
        selection = {};
        commitSelection();
    }

    function commitSelection() {
        // todo make difference between regions blocks and record blocks
        localStorage.setItem('documentSet', JSON.stringify(selection));
    }

    function removeFromSelection(blockId) {
        const { [blockId]: _, ...rest } = selection;
        selection = rest;
        removeAnimation = true;
        setTimeout(() => removeAnimation = false, 300);
        commitSelection();
    }


    function addToSelection(block) {
        // todo add only id and title to selection?
        selection = { ...selection, [block.id]: block };
        addAnimation = true;
        setTimeout(() => addAnimation = false, 300);
        commitSelection();
    }

    $: {
        console.log(blocks);
    }


    function handleToggleSelection(event) {
        const { block } = event.detail;

        if (!isBlockSelected(block)) {
            addToSelection(block);
        } else {
            removeFromSelection(block.id);
        }
    }

</script>

<style>
    .set-container {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        position: fixed;
        bottom: 0;
        right: 0;
        z-index: 1;
    }
    #set-btn {
        border-radius: 0;
    }
    @keyframes addAnimation {
        0%, 100% { transform: translateY(0); }
        25% { transform: translateY(-7px); }
        75% { transform: translateY(7px); }
    }

    @keyframes removeAnimation {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }

    .add-animation span {
        animation: addAnimation 0.3s ease-in-out;
    }

    .remove-animation span {
        animation: removeAnimation 0.3s ease-in-out;
    }
</style>

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

<div>
    {#each blocks as block (block.id)}
        <Block {block} {appLang} on:toggleSelection={handleToggleSelection} isSelected={isBlockSelected(block)}/>
    {/each}
</div>

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
            <table class="table pl-2 is-fullwidth">
                <tbody>
                {#each Object.entries(selection) as [id, meta]}
                    <tr>
                        <th class="is-narrow is-3">
                            <span class="tag px-2 py-1 mb-1 is-dark is-rounded">#{id}</span>
                        </th>
                        <td>
                            <a href="/{meta.url}" target="_blank">{meta.title}</a>
                        </td>
                        <td class="is-narrow">
                            <button class="delete" aria-label="close" on:click={() => removeFromSelection(id)}></button>
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
        </section>
        <footer class="modal-card-foot is-centered">
            <div class="buttons">
                <button class="button is-link is-light" on:click={clearSelection}>
                    {appLang === 'en' ? 'Clear selection' : 'Vider la sélection'}
                </button>
                <button class="button is-link" on:click={saveSelection}>
                    <i class="fa-solid fa-floppy-disk"></i>
                    {appLang === 'en' ? 'Save selection' : 'Sauvegarder la sélection'}
                </button>
            </div>
        </footer>
    </div>
</div>

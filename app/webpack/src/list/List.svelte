<script>
    import Block from './Block.svelte';

    export let blocks = [];
    export let appLang = 'en';

    let selection = {};
    $: selectionLength = Object.keys(selection).length;
    // $: if (selectionLength >= 10) {
    //     alert('Do you wish to save your selection?')
    // }

    let isBlockSelected = (block) => selection.hasOwnProperty(block.id);

    function saveSelection() {
        // api call to save set in database
    }

    function removeFromSelection(blockId) {
        const { [blockId]: _, ...rest } = selection;
        selection = rest;
    }


    function addToSelection(block) {
        selection = { ...selection, [block.id]: block };
        // make block selected
        // make sure block is not already in selection
        // create btn to remove from selection
        // animate selection icon
        // update localStorage

        console.log(selection);
    }

    function handleToggleSelection(event) {
        const { block } = event.detail;

        if (!isBlockSelected(block)) {
            addToSelection(block);
        } else {
            removeFromSelection(block.id);
        }
    }

    function viewSelection() {
        // display blocks and regions in selection
        // display empty selection if none selected
        // display selection modal
        // add btn to discard/save selection
        // link to treatment form
    }

    function checkout() {
        alert('Checkout not implemented yet.');
    }

</script>

<!--{#await promise}
    <p>...waiting</p>
{:then number}
    <p>promise has resolved to {number}</p>
{:catch error}
	<p>{error}</p>
{/await}-->

<div class="button-container">
    <button on:click={viewSelection} class="js-modal-trigger" data-target="selection-modal">
        <i class="fa-solid fa-book-bookmark"></i>
        (<span id="selection-count">{selectionLength}</span>)
    </button>
</div>

<div>
    {#each blocks as block (block.id)}
        <Block {block} {appLang} on:toggleSelection={handleToggleSelection} bind:isSelected={block.isSelected}/>
    {/each}
</div>

<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"></div>
    <div class="modal-content">
        <header class="modal-card-head">
            <i class="fa-solid fa-book-bookmark"></i>
            {appLang === 'en' ? 'Selected documents' : 'Documents sélectionnés'}
            <button class="delete" aria-label="close"></button>
        </header>
        <section class="modal-card-body">
            <ul id="selected-blocks" class="list-group">
                <!-- Selection items will be injected here by JavaScript -->
            </ul>
        </section>
<!--        <footer class="modal-card-foot">-->
<!--            <div class="buttons">-->
<!--                <button class="button is-link is-light">Fermer</button>-->
<!--                <button class="button is-link" onclick="checkout()">-->
<!--                    <i class="fa-solid fa-floppy-disk"></i>-->
<!--                    Enregistrer le Panier-->
<!--                </button>-->
<!--            </div>-->
<!--        </footer>-->
        <button class="modal-close is-large" aria-label="close"></button>
    </div>
</div>

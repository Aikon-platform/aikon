<script>
    import Block from './Block.svelte';

    export let blocks = [];
    export let appLang = 'en';

    let selection = JSON.parse(localStorage.getItem('documentSet')) ?? {};
    $: selectionLength = Object.keys(selection).length;
    // $: if (selectionLength >= 10) {
    //     alert('Do you wish to save your selection?')
    // }

    $: isBlockSelected = (block) => selection.hasOwnProperty(block.id);

    function saveSelection() {
        // api call to save set in database
    }

    function commitSelection() {
        localStorage.setItem('documentSet', JSON.stringify(selection));
    }

    function removeFromSelection(blockId) {
        const { [blockId]: _, ...rest } = selection;
        selection = rest;
        // TODO make block aware that is not selected anymore
        const setBtn = document.getElementById('set-btn')
        setBtn.classList.add('remove-animation');
        setTimeout(() => setBtn.classList.remove('remove-animation'), 500);
        commitSelection();
    }


    function addToSelection(block) {
        selection = { ...selection, [block.id]: block };
        const setBtn = document.getElementById('set-btn')
        setBtn.classList.add('add-animation');
        setTimeout(() => setBtn.classList.remove('add-animation'), 500);
        commitSelection();
    }

    function handleToggleSelection(event) {
        const { block } = event.detail;

        if (!isBlockSelected(block)) {
            addToSelection(block);
        } else {
            removeFromSelection(block.id);
        }
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
        50% { transform: translateY(-25px); }
    }

    @keyframes removeAnimation {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-25px); }
        75% { transform: translateX(25px); }
    }

    .add-animation {
        animation: addAnimation 0.5s ease-in-out;
    }

    .remove-animation {
        animation: removeAnimation 0.5s ease-in-out;
    }
</style>

<div class="set-container">
    <button id="set-btn" class="button px-5 py-4 is-link js-modal-trigger" data-target="selection-modal">
        <i class="fa-solid fa-book-bookmark"></i>
        {appLang === 'en' ? 'Selection' : 'Sélection'}
        (<span id="selection-count">{selectionLength}</span>)
    </button>
</div>

<div>
    {#each blocks as block (block.id)}
        <Block {block} {appLang} on:toggleSelection={handleToggleSelection} isSelected={isBlockSelected(block)}/>
        <!--bind:isSelected={block.isSelected}-->
    {/each}
</div>

<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"></div>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <i class="fa-solid fa-book-bookmark"></i>
                {appLang === 'en' ? 'Selected documents' : 'Documents sélectionnés'}
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
                            <a href="/{meta.class.toLowerCase()}/{id}" target="_blank">{meta.title}</a>
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

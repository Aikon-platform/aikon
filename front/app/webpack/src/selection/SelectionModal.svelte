<script>
    import { closeModal } from '../utils.js';
    import SelectionFooter from "./SelectionFooter.svelte";

    export let selectionStore;
    const { selectionTitle, updateTitle, save } = selectionStore;
    export let selectionLength = false;

    let isEditing = false;
    let titleInput;
    let currentTitle;

    function startEditing() {
        isEditing = true;
        currentTitle = $selectionTitle;
        // todo display changes of the title on the Item component as well + in the selection record list as well
        setTimeout(() => titleInput && titleInput.focus(), 0);
    }

    function handleKeydown(event) {
        if (event.key === 'Enter') {
            finishEditing();
        }
    }

    function finishEditing() {
        isEditing = false;
        updateTitle(currentTitle);
        save();
    }
</script>

<div id="selection-modal" class="modal fade" use:closeModal tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"/>
    <div class="modal-content">
        <div class="modal-card-head media mb-0 is-middle">
            <div class="title is-4 mb-0 media-content">
                <i class="fa-solid fa-book-bookmark"></i>
                {#if isEditing}
                    <input
                        bind:this={titleInput}
                        bind:value={currentTitle}
                        on:keydown={handleKeydown}
                        on:blur={finishEditing}
                        class="input selection-title"
                    />
                {:else}
                    <span on:click={startEditing} on:keyup={null}>
                        {$selectionTitle}
                        <span class="pl-3 smaller has-text-link">
                            <i class="fas fa-edit"/>
                        </span>
                    </span>
                {/if}
                ({selectionLength})
            </div>
            <button class="delete media-left" aria-label="close"/>
        </div>
        <section class="modal-card-body">
            <slot/>
        </section>
        <SelectionFooter {selectionStore}/>
    </div>
</div>

<style>
    .input:focus {
        box-shadow: none;
    }
    .selection-title {
        margin-top: -0.2rem;
        padding-bottom: 0.75rem;
        padding-left: 0.25rem;
        width: 75%;
        height: 2rem;
        display: inline-block;
        font-size: 1.4rem;
        border: none;
        border-bottom: 1px solid var(--bulma-link);
        border-radius: 0;
    }
</style>

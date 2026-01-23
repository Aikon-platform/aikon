<script>
    import { closeModal } from '../utils.js';
    import SelectionFooter from "./SelectionFooter.svelte";

    import { recordsSelection } from "./selectionStore.js";
    import { appLang, userId, isSuperuser } from "../constants.js";
    const { selected } = recordsSelection;

    export let selectionStore;
    export let selectionLength = false;

    const { selectionTitle, updateTitle, updatePublic, save } = selectionStore;

    $: ownerId = $selected?.owner_id;
    $: isOwner = isSuperuser || ownerId === userId;

    let isEditing = false;
    let titleInput;
    let currentTitle;

    function startEditing() {
        isEditing = true;
        currentTitle = $selectionTitle;
        setTimeout(() => titleInput?.focus(), 0);
    }

    function handleKeydown(event) {
        if (event.key === 'Enter') finishEditing();
    }

    function finishEditing() {
        isEditing = false;
        updateTitle(currentTitle);
        save();
    }

    $: selectedUsers = Object.entries($selected?.User || {})
        .map(([id, meta]) => ({
            id: Number(id),
            username: meta.title
        }));

    let userQuery = "";
    let userResults = [];

    async function searchUsers() {
        if (userQuery.trim().length < 1) {
            userResults = [];
            return;
        }

        const response = await fetch(
            `${window.location.origin}/search/user?q=${encodeURIComponent(userQuery)}`
        );

        const data = await response.json();
        userResults = data.users || [];
    }

    function addUser(user) {
        selectionStore.add({
            id: user.id,
            class: "User",
            title: user.username
        });

        userQuery = "";
        userResults = [];
    }

    function removeUser(id) {
        selectionStore.remove(id, "User");
    }
</script>


<div
    id="selection-modal"
    class="modal fade"
    use:closeModal
    tabindex="-1"
    aria-labelledby="selection-modal-label"
    aria-hidden="true"
>
    <div class="modal-background" />

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
                            <i class="fas fa-edit" />
                        </span>
                    </span>
                {/if}

                ({selectionLength})
            </div>

            <button class="delete media-left" aria-label="close" />
        </div>

        <section class="modal-card-body">
            <slot />

            <h4>{appLang === 'en' ? 'Shared with' : 'Partagé avec'}</h4>
            <div class="field is-grouped is-grouped-multiline">
                {#each selectedUsers as user (user.id)}
                    <div class="tags has-addons">
                        <span class="tag">
                            {user.username}
                        </span>
                        {#if isOwner}
                            <button
                                class="tag is-delete"
                                on:click={() => removeUser(user.id)}
                            >
                            </button>
                        {/if}
                    </div>
                {/each}
            </div>

            {#if isOwner}
                <div class="dropdown is-active">
                    <div class="dropdown-trigger">
                        <div class="field">
                            <p class="control is-expanded has-icons-right">
                                <input
                                    class="input"
                                    placeholder="Search users…"
                                    bind:value={userQuery}
                                    on:input={searchUsers}
                                />
                                <span class="icon is-small is-right"><i class="fas fa-search"></i></span>
                            </p>
                        </div>
                    </div>
                    {#if userResults.length > 0}
                        <div class="dropdown-menu" id="dropdown-menu" role="menu">
                            <div class="dropdown-content">
                                {#each userResults as user}
                                    <div class="dropdown-item"
                                        on:click={() => addUser(user)} on:keydown={null}>
                                        {user.username}
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/if}
                </div>

                <div class="field mt-3 is-right">
                    <label class="checkbox">
                        <input
                            type="checkbox"
                            checked={$selected?.is_public}
                            on:change={(e) => updatePublic(e.target.checked)}
                        />
                        {appLang === 'en' ? 'Make public' : 'Rendre public'}
                    </label>
                </div>
            {/if}
        </section>

        <SelectionFooter {selectionStore} />
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
        font-size: 1.4rem;
        border: none;
        border-bottom: 1px solid var(--bulma-link);
        border-radius: 0;
    }

    .tags:last-of-type {
        margin-bottom: 0.75em;
    }
</style>

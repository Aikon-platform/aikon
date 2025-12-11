<script>
    import { selectionStore } from "./selectionStore.js";
    const { selectionTitle, updateTitle, save, selection } = selectionStore;
    import SelectionFooter from "./SelectionFooter.svelte";

    export let isRegion = false;
    export let selectionLength = false;

    let isEditing = false;
    let titleInput;
    let currentTitle;

    function startEditing() {
        isEditing = true;
        currentTitle = $selectionTitle(isRegion);
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
        updateTitle(currentTitle, isRegion);
        save(isRegion);
    }

    let userQuery = "";
    let userResults = [];
    let selectedUsers = [];

    $: {
        const set = $selection(isRegion);
        const storeUsers = set.selected?.User || {};

        selectedUsers = Object.entries(storeUsers).map(([id, meta]) => ({
            id: Number(id),
            username: meta.title
        }));
    }

    async function searchUsers() {
        if (userQuery.trim().length < 1) {
            userResults = [];
            return;
        }

        const url = `${window.location.origin}/search/user?q=${encodeURIComponent(userQuery)}`;
        const response = await fetch(url);
        const data = await response.json();

        userResults = data.users || [];
    }

    function addUser(user) {
        if (!selectedUsers.find(u => u.id === user.id)) {
            selectedUsers = [...selectedUsers, user];

            selectionStore.add({
                id: user.id,
                class: "User",
                title: user.username
            });
        }

        userQuery = "";
        userResults = [];
    }

    function removeUser(id) {
        selectedUsers = selectedUsers.filter(u => u.id !== id);
        selectionStore.remove(id, "User");
    }
</script>

<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
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
                        {$selectionTitle(isRegion)}
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

            <h4 class="title is-6 mt-3 mb-2">Shared with</h4>
            <div class="field is-grouped is-grouped-multiline">
                {#each selectedUsers as user (user.id)}
                    <div class="tags has-addons">
                        <span class="tag">
                            {user.username}
                        </span>
                        <button
                            class="tag is-delete"
                            on:click={() => removeUser(user.id)}
                        >
                        </button>
                    </div>
                {/each}
            </div>

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
        </section>

        <SelectionFooter {isRegion}/>
    </div>
</div>

<style>
    .input:focus {
        box-shadow: none;
    }
    .selection-title {
        margin-top: -0.2rem;
        padding-bottom: 0.75rem;
        width: 75%;
        font-size: 1.4rem;
        border: none;
        border-bottom: 1px solid var(--bulma-link);
        border-radius: 0;
    }
</style>

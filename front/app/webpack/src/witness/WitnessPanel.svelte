<script>
    export let viewTitle = "";
    export let witness = {};
    export let editUrl = "";

    let openContents = new Set();

    function showContent(id) {
        if (openContents.has(id)) {
            openContents.delete(id);
        } else {
            openContents.add(id);
        }
        openContents = new Set(openContents);
    }
</script>

<div class="panel box">
    <div class="content">
        <h2 class="title is-4 mb-4">
            {viewTitle}
            <a
                href={editUrl}
                class="edit-btn button is-small is-rounded is-link px-3 ml-2 mt-1"
                title="Edit"
            >
                <span class="iconify" data-icon="entypo:edit"></span>
            </a>
        </h2>

        {#each Object.entries(witness.metadata_full.wit) as [key, value]}
            <span class="witness-key">{key}</span><br />
            <span class="witness-value">{value}</span>
        {/each}

        {#if witness.metadata_full.contents?.length}
            <h3 class="title is-5 mb-3">Contents</h3>

            {#each witness.metadata_full.contents as content, id}
                <div class="mb-3">
                    <div
                        class="is-flex is-justify-content-space-between is-clickable witness-key"
                        on:click={() => showContent(id)}
                        on:keypress={() => showContent(id)}
                    >
                        {content.title}
                        <i class="fa-solid fa-chevron-down"></i>
                    </div>

                    {#if openContents.has(id)}
                        <div class="mt-2 pl-3">
                            {#each Object.entries(content.content) as [key, value]}
                                <div class="witness-value"><b>{key}:</b> {value}</div>
                            {/each}
                        </div>
                    {/if}
                </div>
            {/each}
        {/if}
    </div>
</div>

<style>
.panel {
    height: 80vh;
    overflow-y: auto;
}

.witness-key {
    display: block;
    font-weight: bold;
    border-bottom: 1px solid var(--bulma-border);
    padding: 10px 0;
}
</style>

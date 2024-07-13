<script>
    export let store;
    const { currentPage } = store;

    export let nbOfItems;
    export let pageLength = 50;
    const maxPage = Math.ceil(nbOfItems / pageLength);
</script>

{#if maxPage > 1}
<nav class="pagination is-centered" aria-label="pagination">
    <ul class="pagination-list">
        {#if $currentPage > 1}
            <li><a class="pagination-link" on:click|preventDefault={() => store.handlePageUpdate(1)} href={null}>1</a></li>
            {#if $currentPage - 1 > 1}
                <li><span class="pagination-ellipsis">&hellip;</span></li>
                <li><a class="pagination-link" on:click|preventDefault={() => store.handlePageUpdate($currentPage - 1)} href={null}>{$currentPage - 1}</a></li>
            {/if}
        {/if}
        <li><a class="pagination-link is-current" on:click|preventDefault={() => store.handlePageUpdate($currentPage)} href={null}>{$currentPage}</a></li>
        {#if $currentPage < maxPage}
            {#if $currentPage + 1 < maxPage}
                <li><a class="pagination-link" on:click|preventDefault={() => store.handlePageUpdate($currentPage + 1)} href={null}>{$currentPage + 1}</a></li>
                <li><span class="pagination-ellipsis">&hellip;</span></li>
            {/if}
            <li><a class="pagination-link" on:click|preventDefault={() => store.handlePageUpdate(maxPage)} href={null}>{maxPage}</a></li>
        {/if}
    </ul>
</nav>
{/if}

<script>
    import {pageSize} from "./constants.js";

    export let store;
    const { currentPage } = store;

    export let nbOfItems;
    export let pageLength = pageSize;
    $: maxPage = pageLength < pageSize ? 1 : Math.ceil(nbOfItems / pageLength);
    $: multiplePages = maxPage > 1 || nbOfItems > pageLength
    // todo fix maxPage that can be undefined / Nan
</script>

{#if multiplePages}
<nav class="pagination is-centered mb-2" aria-label="pagination">
    <ul class="pagination-list ml-0">
        {#if $currentPage > 1}
            <li><a class="pagination-link" on:click|preventDefault={() => store.handlePageUpdate(1)} href={null}>1</a></li>
            {#if $currentPage - 1 > 1}
                {#if $currentPage - 1 > 2}
                    <li><span class="pagination-ellipsis">&hellip;</span></li>
                {/if}
                <li><a class="pagination-link" on:click|preventDefault={() => store.handlePageUpdate($currentPage - 1)} href={null}>{$currentPage - 1}</a></li>
            {/if}
        {/if}
        <li><a class="pagination-link is-current" on:click|preventDefault={() => store.handlePageUpdate($currentPage)} href={null}>{$currentPage}</a></li>
        {#if $currentPage < maxPage}
            {#if $currentPage + 1 < maxPage}
                <li><a class="pagination-link" on:click|preventDefault={() => store.handlePageUpdate($currentPage + 1)} href={null}>{$currentPage + 1}</a></li>
                {#if $currentPage + 2 < maxPage}
                    <li><span class="pagination-ellipsis">&hellip;</span></li>
                {/if}
            {/if}
            <li><a class="pagination-link" on:click|preventDefault={() => store.handlePageUpdate(maxPage)} href={null}>{maxPage}</a></li>
        {/if}
    </ul>
</nav>
{/if}
<div class="is-size-7 is-center mb-4 {!multiplePages ? 'mt-4' : ''}">
    {$currentPage * pageLength - pageLength + 1} - {Math.min($currentPage * pageLength, nbOfItems)} / {nbOfItems}
</div>

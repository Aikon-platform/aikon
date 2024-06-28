<script>
    import {createEventDispatcher} from "svelte";

    const dispatch = createEventDispatcher();
    export let pageNb;
    export let maxPage;

    function pageUpdate(pageNb) {
        dispatch('pageUpdate', { pageNb });
    }
</script>

{#if maxPage > 1}
<nav class="pagination is-centered" aria-label="pagination">
    <ul class="pagination-list">
        {#if pageNb > 1}
            <li><a class="pagination-link" on:click|preventDefault={() => pageUpdate(1)} href={null}>1</a></li>
            {#if pageNb - 1 > 1}
                <li><span class="pagination-ellipsis">&hellip;</span></li>
                <li><a class="pagination-link" on:click|preventDefault={() => pageUpdate(pageNb - 1)} href={null}>{pageNb - 1}</a></li>
            {/if}
        {/if}
        <li><a class="pagination-link is-current" on:click|preventDefault={() => pageUpdate(pageNb)} href={null}>{pageNb}</a></li>
        {#if pageNb < maxPage}
            {#if pageNb + 1 < maxPage}
                <li><a class="pagination-link" on:click|preventDefault={() => pageUpdate(pageNb + 1)} href={null}>{pageNb + 1}</a></li>
                <li><span class="pagination-ellipsis">&hellip;</span></li>
            {/if}
            <li><a class="pagination-link" on:click|preventDefault={() => pageUpdate(maxPage)} href={null}>{maxPage}</a></li>
        {/if}
    </ul>
</nav>
{/if}

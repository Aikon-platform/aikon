<script>
    import {getColNb} from "./utils.js";

    export let useGrid = true;
    let innerWidth = 0;
    $: colNb = getColNb(innerWidth);
</script>

<svelte:window bind:innerWidth/>

<tr>
    <th class="is-3 center-flex is-narrow" style="width: 15vw">
        <div class="content-wrapper py-5">
            <slot name="row-header"/>
        </div>
    </th>
    <td class="p-5 is-fullwidth">
        {#if useGrid}
            <div class="fixed-grid has-{colNb}-cols">
                <div class="grid is-gap-2">
                    <slot name="row-body"/>
                </div>
            </div>
        {:else}
            <slot name="row-body"/>
        {/if}
    </td>
</tr>

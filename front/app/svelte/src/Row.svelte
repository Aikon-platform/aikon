<!-- @migration-task-ok Error while migrating Svelte code: This migration would change the name of a slot (row-header to row_header) making the component unusable -->
<script>
    import {getColNb} from "./utils.js";

    let { useGrid = true, rowHeader, rowBody } = $props();
    let innerWidth = $state(0);
    let colNb = $derived(getColNb(innerWidth));
</script>

<svelte:window bind:innerWidth={innerWidth} />

<tr>
    <th class="is-3 center-flex is-narrow" style="width: 15vw">
        <div class="content-wrapper py-5">
            {@render rowHeader()}
        </div>
    </th>
    <td class="p-5 is-fullwidth">
        {#if useGrid}
            <div class="fixed-grid has-{colNb}-cols">
                <div class="grid is-gap-2">
                    {@render rowBody()}
                </div>
            </div>
        {:else}
            {@render rowBody()}
        {/if}
    </td>
</tr>

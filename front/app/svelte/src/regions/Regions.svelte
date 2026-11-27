<script>
    import { RegionItem } from "./types.js";
    import RegionCard from "./RegionCard.svelte";
    import RegionModal from "./modal/RegionModal.svelte";
    import RegionTabs from "./modal/RegionTabs.svelte";

    import {regionsSelection} from "../selection/selectionStore.js";



    /**
     * @typedef {Object} Props
     * @property {any} [selectionStore]
     * @property {RegionItemType[]} [items]
     * @property {number|"full"} [height]
     * @property {boolean} [selectable]
     * @property {boolean} [copyable]
     */

    /** @type {Props} */
    let {
        selectionStore = regionsSelection,
        items = [],
        height = 96,
        selectable = true,
        copyable = true
    } = $props();

    let modalOpen = $state(false);
    let modalIndex = $state(0);

    const handleOpenModal = (e) => {
        modalIndex = e.detail.index ?? 0;
        modalOpen = true;
    };

    const handleNavigate = (e) => {
        modalIndex = e.detail.index;
    };
</script>

{#each Object.values(items) as item, i (item.id)}
    <RegionCard item={new RegionItem(item)} index={i}
            {height} {copyable} {selectable} {selectionStore}
            on:openModal={handleOpenModal}/>
{/each}

<RegionModal {items} bind:currentIndex={modalIndex} bind:open={modalOpen} on:navigate={handleNavigate}>
    {#snippet children({ item: currentItem })}

            <RegionTabs item={currentItem} {copyable}/>

    {/snippet}
</RegionModal>

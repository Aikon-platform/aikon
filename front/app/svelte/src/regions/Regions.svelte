<script>
    import { RegionItem } from "./types.js";
    import RegionCard from "./RegionCard.svelte";
    import RegionModal from "./modal/RegionModal.svelte";
    import RegionTabs from "./modal/RegionTabs.svelte";

    import {regionsSelection} from "../selection/selectionStore.js";
    export let selectionStore = regionsSelection;

    /** @type {RegionItemType[]} */
    export let items = [];
     /** @type {number|"full"} */
    export let height = 96;
    export let selectable = true;
    export let copyable = true;

    let modalOpen = false;
    let modalIndex = 0;

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
    <svelte:fragment let:item={currentItem}>
        <RegionTabs item={currentItem} {copyable}/>
    </svelte:fragment>
</RegionModal>

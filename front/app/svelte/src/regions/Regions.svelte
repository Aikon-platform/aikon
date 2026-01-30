<script>
    import {appLang} from "../constants.js";
    import { RegionItem } from "./types.js";
    import RegionCard from "./RegionCard.svelte";
    import PageView from "./modal/PageView.svelte";
    import RegionModal from "./modal/RegionModal.svelte";
    import Tabs from "../ui/Tabs.svelte";

    import {regionsSelection} from "../selection/selectionStore.js";
    export let selectionStore = regionsSelection;
    const { isSelected } = selectionStore;

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

    $: tabs = [
        { id: "region", label: appLang === "en" ? "Main view" : "Vue principale" },
        { id: "page", label: appLang === "en" ? "Page View" : "Vue de la page" },
    ];
</script>

{#each Object.values(items) as item, i (item.id)}
    <RegionCard item={new RegionItem(item)} index={i}
            {height} {copyable} {selectable} {selectionStore}
            on:openModal={handleOpenModal}/>
{/each}

<RegionModal {items} bind:currentIndex={modalIndex}
             bind:open={modalOpen} on:navigate={handleNavigate}>
    <svelte:fragment let:item={currentItem}>
        <Tabs {tabs} let:activeTab>
            {#if activeTab === "region"}
                <div class="modal-region">
                    <RegionCard item={currentItem} height="full" isInModal={true} selectable={false}/>
                </div>
            {:else if activeTab === "page"}
                <PageView item={currentItem}/>
            {/if}
        </Tabs>
    </svelte:fragment>
</RegionModal>

<style>
    .modal-region {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .modal-region :global(.region) {
        height: 100%;
    }
</style>

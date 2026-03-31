<script>
    import {appLang} from "../constants.js";
    import { RegionItem } from "./types.js";
    import RegionCard from "./RegionCard.svelte";
    import PageView from "./modal/PageView.svelte";
    import RegionModal from "./modal/RegionModal.svelte";
    import Tabs from "../ui/Tabs.svelte";

    import {regionsSelection} from "../selection/selectionStore.js";
    import QueryExpansionView from "./modal/QueryExpansionView.svelte";
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

    const tabs = [
        { id: "region", label: appLang === "en" ? "Main view" : "Vue principale" },
        { id: "page", label: appLang === "en" ? "Page View" : "Vue de la page" },
        { id: "matches", label: appLang === "en" ? "Matches" : "Correspondances" }
    ];
</script>

{#each Object.values(items) as item, i (item.id)}
    <RegionCard item={new RegionItem(item)} index={i}
            {height} {copyable} {selectable} {selectionStore}
            on:openModal={handleOpenModal}/>
{/each}

<RegionModal {items} bind:currentIndex={modalIndex} bind:open={modalOpen} on:navigate={handleNavigate}>
    <svelte:fragment let:item={currentItem}>
        <Tabs {tabs} let:activeTab>
            {#if activeTab === "region"}
                <div class="modal-region">
                    <RegionCard item={currentItem} height="full" isInModal={true} {copyable} selectable={false}/>
                </div>
            {:else if activeTab === "page"}
                <PageView item={currentItem}/>
            {:else if activeTab === "matches"}
                {#key currentItem.img}
                    <QueryExpansionView item={currentItem}/>
                {/key}
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

<script>
    import Tabs from "../../ui/Tabs.svelte";
    import RegionCard from "../RegionCard.svelte";
    import PageView from "./PageView.svelte";
    import ComparisonView from "./ComparisonView.svelte";
    import QueryExpansionView from "./QueryExpansionView.svelte";
    import DuplicatesView from "./DuplicatesView.svelte";
    import { i18n } from "../../utils.js";
    import { setContext } from "svelte";
    import { RegionItem } from "../types.js";

    const allTabs = [
        { id: "region", label: i18n("mainView") },
        { id: "page", label: i18n("pageView") },
        { id: "similarity", label: i18n("similarityView") },
        { id: "duplicates", label: i18n("duplicatesView") },
        { id: "matches", label: i18n("matchesView") },
    ];

    /** @type {import("../types.js").RegionItemType} */
    export let item;
    /** @type {{qImg?: string, sImg: string}|null} without qImg, the current item is the query */
    export let comparison = null;
    export let activeTab = "region";
    export let copyable = true;
    export let showNav = true;
    export let tabs = allTabs.map(({ id }) => id);

    setContext("compareWith", (sImg) => {
        comparison = { sImg };
        activeTab = "similarity";
    });
    $: pair = comparison && { qImg: comparison.qImg ?? new RegionItem(item).fullImg, sImg: comparison.sImg };
    $: visibleTabs = allTabs.filter(({ id }) => tabs.includes(id) && (id !== "similarity" || comparison));
    $: if (activeTab === "similarity" && !comparison) activeTab = "region";
</script>

<Tabs tabs={visibleTabs} bind:activeTab>
    {#if activeTab === "region"}
        <div class="modal-region">
            <RegionCard {item} height="full" isInModal={true} {copyable} selectable={false}/>
        </div>
    {:else if activeTab === "page"}
        <PageView {item} {showNav}/>
    {:else if activeTab === "similarity" && pair}
        <ComparisonView qImg={pair.qImg} sImg={pair.sImg}/>
    {:else if activeTab === "duplicates"}
        <DuplicatesView {item}/>
    {:else if activeTab === "matches"}
        {#key item.img}
            <QueryExpansionView {item}/>
        {/key}
    {/if}
</Tabs>

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

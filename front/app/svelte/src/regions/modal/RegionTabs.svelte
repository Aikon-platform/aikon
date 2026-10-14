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

    let compared = null;
    setContext("compareWith", (sImg) => {
        compared = { sImg };
        activeTab = "similarity";
    });

    $: regionItem = new RegionItem(item);
    $: img = regionItem.fullImg;
    $: img, compared = null;
    $: active = compared ?? comparison;
    $: pair = active && { qImg: active.qImg ?? img, sImg: active.sImg };
    $: visibleTabs = allTabs.filter(({ id }) => tabs.includes(id) && (id !== "similarity" || pair));
    $: if (activeTab === "similarity" && !pair) activeTab = "region";
</script>

<Tabs tabs={visibleTabs} bind:activeTab>
    {#if activeTab === "region"}
        <div class="modal-context-outer is-flex-direction-column pb-4">
            <div class="has-text-centered mb-2">
                <a class="tag button is-small has-text-grey mt-3" href={regionItem.witnessUrl} target="_blank">
                    {i18n("Witness")} #{regionItem.witnessId}
                </a>
            </div>
            <div class="modal-context-wrapper mb-3">
                <div class="modal-region modal-context-full-page">
                    <RegionCard {item} height="full" isInModal={true} {copyable} selectable={false}/>
                </div>
            </div>
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

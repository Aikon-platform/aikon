<script>
    import { run } from 'svelte/legacy';

    import Tabs from "../../ui/Tabs.svelte";
    import RegionCard from "../RegionCard.svelte";
    import PageView from "./PageView.svelte";
    import ComparisonView from "./ComparisonView.svelte";
    import QueryExpansionView from "./QueryExpansionView.svelte";
    import DuplicatesView from "./DuplicatesView.svelte";
    import { i18n } from "../../utils.svelte.js";
    import { setContext } from "svelte";
    import { RegionItem } from "../types.js";

    const allTabs = [
        { id: "region", label: i18n("mainView") },
        { id: "page", label: i18n("pageView") },
        { id: "similarity", label: i18n("similarityView") },
        { id: "duplicates", label: i18n("duplicatesView") },
        { id: "matches", label: i18n("matchesView") },
    ];



    /**
     * @typedef {Object} Props
     * @property {import("../types.js").RegionItemType} item
     * @property {{qImg?: string, sImg: string}|null} [comparison]
     * @property {string} [activeTab]
     * @property {boolean} [copyable]
     * @property {boolean} [showNav]
     * @property {any} [tabs]
     */

    /** @type {Props} */
    let {
        item,
        comparison = null,
        activeTab = $bindable("region"),
        copyable = true,
        showNav = true,
        tabs = allTabs.map(({ id }) => id)
    } = $props();

    let compared = $state(null);
    setContext("compareWith", (sImg) => {
        compared = { sImg };
        activeTab = "similarity";
    });

    let regionItem = $derived(new RegionItem(item));
    let img = $derived(regionItem.fullImg);
    run(() => {
        img, compared = null;
    });
    let active = $derived(compared ?? comparison);
    let pair = $derived(active && { qImg: active.qImg ?? img, sImg: active.sImg });
    let visibleTabs = $derived(allTabs.filter(({ id }) => tabs.includes(id) && (id !== "similarity" || pair)));
    run(() => {
        if (activeTab === "similarity" && !pair) activeTab = "region";
    });
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

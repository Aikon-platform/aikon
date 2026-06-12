<script>
    import { createEventDispatcher } from "svelte";
    import RegionCard from "../regions/RegionCard.svelte";
    import RegionModal from "../regions/modal/RegionModal.svelte";
    import PageView from "../regions/modal/PageView.svelte";
    import RightClick from "../ui/RightClick.svelte";
    import Tabs from "../ui/Tabs.svelte";
    import { i18n, withLoading, showMessage } from "../utils.js";
    import { appName, csrfToken } from "../constants.js";
    import QueryExpansionView from "../regions/modal/QueryExpansionView.svelte";
    import CategoryToolbar from "../regions/similarity/CategoryToolbar.svelte";

    export let matches = [];
    export let columns = [];
    export let cardHeight = 96;
    export let isInStemma = false;
    export let hideEmpty = false;
    export let clusterStore;
    /** Map<"id1-id2", category> of current pair categories, for selection state */
    export let pairCat = new Map();

    // anchor image is the first of the list
    $: anchorImageId = isInStemma ? displayMatches[0]?.[0]?.images?.[0]?.id ?? null : null;

    const dispatch = createEventDispatcher();
    const baseUrl = window.location.origin;

    const pairCategory = (a, b) => pairCat.get(`${a}-${b}`) ?? pairCat.get(`${b}-${a}`) ?? null;

    const rowPairs = row => {
        const anchor = row[0]?.images?.[0];
        if (!anchor) return [];
        return row.slice(1).flatMap(cell =>
            (cell?.images ?? []).map(img => ({ img_1: anchor.id, img_2: img.id }))
        );
    };

    // _pairCat arg makes the value a tracked dependency in the template
    const rowCategory = (row, _pairCat) => {
        const pairs = rowPairs(row);
        if (!pairs.length) return null;
        const cats = pairs.map(p => pairCategory(p.img_1, p.img_2));
        return cats.every(c => c === cats[0]) ? cats[0] : null;
    };

    const categorizeRow = (row, category) => {
        const pairs = rowPairs(row);
        if (!pairs.length) return;
        rowCategory(row, pairCat) === category
            ? clusterStore.uncategorizePairBatch(pairs)
            : clusterStore.categorizePairBatch(pairs, category);
    };

    async function userToggleRow(row) {
        const pairs = rowPairs(row);
        if (!pairs.length) return;
        try {
            await Promise.all(pairs.map(p => withLoading(() => fetch(`${baseUrl}/${appName}/add-user-to-pair`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
                body: JSON.stringify(p)
            }))));
        } catch (e) {
            await showMessage(String(e), i18n("error"));
        }
    }
    const tabs = [
        { id: "region", label: i18n("mainView") },
        { id: "page", label: i18n("pageView") },
        { id: "matches", label: i18n("matchesView") },
    ];

    let modalOpen = false;
    let modalIndex = 0;
    let menu = { open: false, x: 0, y: 0, items: [] };

    $: displayMatches = hideEmpty && matches.length > 1
        ? matches.filter(row => row.slice(1).some(c => c))
        : matches;

    $: modalItems = displayMatches.flatMap(row => row.flatMap(c => c?.images ?? []));

    const handleOpenModal = (e) => {
        modalIndex = e.detail.index ?? 0;
        modalOpen = true;
    };

    function onCardContextMenu(e, img, doc) {
        if (!isInStemma || img.id === anchorImageId) return;
        e.preventDefault();
        menu = {
            open: true, x: e.clientX, y: e.clientY,
            items: [{ label: i18n("setAnchor", t), icon: "anchor", action: () => dispatch("anchorselect", { imageId: img.id, baseDocId: doc.id }) }]
        };
    }

    const t = {
        none:      { en: "No matches", fr: "Aucune correspondance" },
        matches:   { en: "matches", fr: "correspondances" },
        setAnchor: { en: "Set as anchor", fr: "Définir comme ancre" },
        anchor:    { en: "Current anchor", fr: "Ancre courante" },
    };
</script>

<div class="matches-scroll">
    {#if !displayMatches.length}
        <p class="has-text-grey is-size-7 p-3">{i18n("none", t)}</p>
    {:else if displayMatches.length === 1}
        {#if displayMatches[0].length !== 1}
            <CategoryToolbar visibleCategories={[1,2,3]}
                selectedCategory={rowCategory(displayMatches[0], pairCat)}
                toggleFct={cat => categorizeRow(displayMatches[0], cat)}
                userToggleFct={() => userToggleRow(displayMatches[0])}/>
        {/if}
        <div class="is-flex is-flex-wrap-wrap is-align-items-flex-start" style="gap: 1rem;">
            {#each displayMatches[0] as cell}
                {#if cell}
                    {#each cell.images as img, k}
                        <div class="is-flex is-flex-wrap-wrap is-flex-direction-column is-align-content-center"
                             on:contextmenu={e => onCardContextMenu(e, img, cell.doc)}>
                            <RegionCard item={img} height={cardHeight} borderColor={cell.doc.color}
                                        borderWidth={img.id === cell.bestImageId ? 7 : 4}
                                        index={cell.indices[k]} selectable={false} copyable={false}
                                        on:openModal={handleOpenModal}>
                                <svelte:fragment slot="actions">
                                    {#if img.id === anchorImageId}
                                        <span class="tag button is-unclickable p-0" title={i18n("anchor", t)}>
                                            <i class="fa-solid fa-anchor"/>
                                        </span>
                                    {/if}
                                </svelte:fragment>
                            </RegionCard>
                            {#if img.canvas}
                                <div class="is-size-7 has-text-grey has-text-centered">
                                    Page {img.canvas}
                                </div>
                            {/if}
                        </div>
                    {/each}
                {/if}
            {/each}
        </div>
    {:else}
        <p class="is-size-7 has-text-grey mb-2">{displayMatches.length} {i18n("matches", t)}</p>
        <table class="table is-fullwidth is-narrow">
            <thead>
                <tr>
                    {#each columns as col}
                        <th>
                            <span class="color-dot" style="background:{col.doc.color}"/>
                            {col.label ?? col.doc.title}
                        </th>
                    {/each}
                    {#if columns.length !== 1}
                        <th style="width: 4em;"/>
                    {/if}
                </tr>
            </thead>
            <tbody>
                {#each displayMatches as row, i (i)}
                    <tr>
                        {#each row as cell, j (j)}
                            <td>
                                {#if cell}
                                    <div class="is-flex is-flex-wrap-wrap is-flex-direction-column is-align-content-center pt-2">
                                        {#each cell.images as img, k}
                                            <div on:contextmenu={e => onCardContextMenu(e, img, cell.doc)}>
                                                <RegionCard item={img} height={cardHeight} index={cell.indices[k]}
                                                            selectable={false} copyable={false}
                                                            on:openModal={handleOpenModal}/>
                                                {#if img.canvas}
                                                    <div class="is-size-7 has-text-grey has-text-centered mb-1">
                                                        Page {img.canvas}
                                                    </div>
                                                {/if}
                                            </div>
                                        {/each}
                                    </div>
                                {/if}
                            </td>
                        {/each}
                        {#if columns.length !== 1}
                            <td>
                                <CategoryToolbar horizontal={false} visibleCategories={[1,2,3]}
                                    selectedCategory={rowCategory(row, pairCat)}
                                    toggleFct={cat => categorizeRow(row, cat)}
                                    userToggleFct={() => userToggleRow(row)}/>
                            </td>
                        {/if}
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}
</div>

<RightClick bind:open={menu.open} x={menu.x} y={menu.y} items={menu.items}/>

<RegionModal items={modalItems} bind:currentIndex={modalIndex} bind:open={modalOpen}>
    <svelte:fragment let:item={currentItem}>
        <Tabs {tabs} let:activeTab>
            {#if activeTab === "region"}
                <div class="modal-region">
                    <RegionCard item={currentItem} height="full" isInModal={true} copyable={true} selectable={false}/>
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
    .color-dot {
        width: 10px; height: 10px; border-radius: 50%;
        display: inline-block; margin-right: 0.4em;
    }
    .matches-scroll {
        min-height: 50vh;
        max-height: 125vh;
        overflow: auto;
    }
    table { table-layout: fixed; }
    td { vertical-align: middle; }
    .modal-region {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .modal-region :global(.region) {
        height: 100%;
    }
    thead th {
        position: sticky;
        top: 0;
        background: var(--bulma-scheme-main);
        z-index: 29;
        border-bottom: var(--bulma-table-cell-border-color) solid 1px !important;
        box-shadow: 0 5px 5px rgba(0, 0, 0, 0.1);
    }
</style>

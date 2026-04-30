<script>
    import RegionCard from "../regions/RegionCard.svelte";
    import RegionModal from "../regions/modal/RegionModal.svelte";
    import PageView from "../regions/modal/PageView.svelte";
    import Tabs from "../ui/Tabs.svelte";
    import { i18n } from "../utils.js";

    /** @type {Array<Array<{images, doc, indices} | null>>} */
    export let matches = [];
    /** @type {Array<{doc, label?: string}>} */
    export let columns = [];
    export let cardHeight = 96;

    const tabs = [
        { id: "region", label: i18n("mainView") },
        { id: "page", label: i18n("pageView") },
    ];

    let modalOpen = false;
    let modalIndex = 0;

    $: modalItems = matches.flatMap(row => row.flatMap(c => c?.images ?? []));

    const handleOpenModal = (e) => {
        modalIndex = e.detail.index ?? 0;
        modalOpen = true;
    };

    const t = {
        none: { en: "No matches", fr: "Aucune correspondance" },
        matches: { en: "matches", fr: "correspondances" },
    };
</script>

<div class="matches-scroll">
    {#if !matches.length}
        <p class="has-text-grey is-size-7 p-3">{i18n("none", t)}</p>
    {:else if matches.length === 1}
        <div class="is-flex is-flex-wrap-wrap is-align-items-flex-start" style="gap: 1rem;">
            {#each matches[0] as cell}
                {#if cell}
                    {#each cell.images as img, k}
                        <RegionCard item={img} height={cardHeight} borderColor={cell.doc.color}
                                    index={cell.indices[k]} selectable={false} copyable={false}
                                    on:openModal={handleOpenModal}/>
                    {/each}
                {/if}
            {/each}
        </div>
    {:else}
        <p class="is-size-7 has-text-grey mb-2">{matches.length} {i18n("matches", t)}</p>
        <table class="table is-fullwidth is-narrow">
            <thead>
                <tr>
                    {#each columns as col}
                        <th>
                            <span class="color-dot" style="background:{col.doc.color}"/>
                            {col.label ?? col.doc.title}
                        </th>
                    {/each}
                </tr>
            </thead>
            <tbody>
                {#each matches as row, i (i)}
                    <tr>
                        {#each row as cell, j (j)}
                            <td>
                                {#if cell}
                                    <div class="is-flex is-flex-wrap-wrap" style="gap: 0.5rem;">
                                        {#each cell.images as img, k}
                                            <RegionCard item={img} height={cardHeight}
                                                        index={cell.indices[k]}
                                                        selectable={false} copyable={false}
                                                        on:openModal={handleOpenModal}/>
                                        {/each}
                                    </div>
                                {/if}
                            </td>
                        {/each}
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}
</div>

<RegionModal items={modalItems} bind:currentIndex={modalIndex} bind:open={modalOpen}>
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
    .color-dot {
        width: 10px; height: 10px; border-radius: 50%;
        display: inline-block; margin-right: 0.4em;
    }
    .matches-scroll {
        max-height: 50vh;
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
        z-index: 30;
        border-bottom: var(--bulma-table-cell-border-color) solid 1px !important;
        box-shadow: 0 5px 5px rgba(0, 0, 0, 0.1);
    }
</style>

<script>
    import RegionCard from "../regions/RegionCard.svelte";
    import { i18n } from "../utils.js";
    import RegionModal from "../regions/modal/RegionModal.svelte";
    import Tabs from "../ui/Tabs.svelte";
    import PageView from "../regions/modal/PageView.svelte";

    /** @type {Array<Array<{image, doc} | null>>} */
    export let matches = [];
    /** @type {Array<{doc, label?: string}>} */
    export let columns = [];
    export let cardHeight = 96;

    $: console.log(matches);

    const tabs = [
        { id: "region", label: i18n("mainView") },
        { id: "page", label: i18n("pageView") },
    ];

    let modalOpen = false;
    let modalIndex = 0;
    const rowCanvas = (row) => row.find(Boolean)?.image?.canvas ?? Infinity;
    $: sortedMatches = [...matches].sort((a, b) => rowCanvas(a) - rowCanvas(b));
    $: modalItems = sortedMatches.flat().filter(Boolean).map(c => c.image);
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
            {#each matches[0] as cell, index}
                {#if cell}
                    <RegionCard item={cell.image} height={cardHeight} borderColor={cell.doc.color} {index}
                                selectable={false} copyable={false} on:openModal={handleOpenModal}/>
                {/if}
            {/each}
        </div>
    {:else}
        <p class="is-size-7 has-text-grey mb-2">{matches.length} {i18n("matches", t)}</p>
        <div class="table-container">
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
                {#each matches as row, i}
                    <tr>
                        {#each row as cell, j}
                            <td>
                                {#if cell}
                                    <RegionCard item={cell.image} height={cardHeight}
                                                borderColor={cell.doc.color}
                                                selectable={false} copyable={false}
                                                index={i + j}
                                                on:openModal={handleOpenModal}/>

                                {/if}
                            </td>
                        {/each}
                    </tr>
                {/each}
                </tbody>
            </table>
        </div>
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
    td { vertical-align: top; }
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

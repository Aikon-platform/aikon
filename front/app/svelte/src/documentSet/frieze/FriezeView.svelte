<script>
    import { writable } from "svelte/store";
    import { i18n } from "../../utils.svelte.js";
    import SplitLayout from "../../ui/SplitLayout.svelte";
    import SpatialFrieze from "./SpatialFrieze.svelte";
    import Matches from "../Matches.svelte";
    import DownloadPng from "../../ui/DownloadPng.svelte";

    let { documentSetStore, clusterStore } = $props();

    const {
        documentNodes, visibleDocuments, visiblePairs, buildFriezeMatches, buildClusterMatches, pairCat
    } = documentSetStore;

    const friezeStub = { nodeTitles: writable({}) };

    let friezeMode = $state("image");
    let selectedFriezeImage = $state(null);
    let selectedCluster = $state(null);

    let documents = $derived($visibleDocuments);
    let matchesData = $derived(selectedCluster
        ? buildClusterMatches(selectedCluster)
        : selectedFriezeImage
            ? buildFriezeMatches(selectedFriezeImage, $visiblePairs)
            : { matches: [], columns: [] });

    const t = {
        title: { en: "Spatial Frieze", fr: "Frise spatiale" },
        matches: { en: "Matches", fr: "Correspondances" },
        byPage: { en: "By page", fr: "Par page" },
        byImage: { en: "By image", fr: "Par image" },
        selectImage: { en: "Click an image in the frieze to view its matches", fr: "Cliquez sur une image de la frise pour voir ses correspondances" },
    };

    function handleImageSelect(e) {
        selectedFriezeImage = e.detail;
        selectedCluster = null;
    }

    function handleClusterSelect(e) {
        selectedCluster = e.detail;
        selectedFriezeImage = null;
    }
</script>

<SplitLayout>
    <!-- @migration-task-ok: migrate this slot by hand, `left-title` is an invalid identifier -->
    {#snippet leftTitle()}
        <div class="is-flex is-justify-content-space-between is-align-items-center">
            <h4 class="title is-6 mb-0">{i18n("title", t)}</h4>
            <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
                <DownloadPng targetId="spatial-frieze" filename="spatial-frieze" svgExport={true}/>
                <div class="select is-small">
                    <select bind:value={friezeMode}>
                        <option value="page">{i18n("byPage", t)}</option>
                        <option value="image">{i18n("byImage", t)}</option>
                    </select>
                </div>
            </div>
        </div>
    {/snippet}
    <!-- @migration-task-ok: migrate this slot by hand, `left-scroll` is an invalid identifier -->
    {#snippet leftScroll()}
        <div>
            <SpatialFrieze
                {documents} {visiblePairs} {documentNodes}
                stemmaStore={friezeStub}
                mode={friezeMode}
                on:imageselect={handleImageSelect}
                on:clusterselect={handleClusterSelect}
            />
        </div>
    {/snippet}

    <!-- @migration-task-ok: migrate this slot by hand, `right-title` is an invalid identifier -->
    {#snippet rightTitle()}
        <div>
            {#if matchesData.matches.length}
                <h4 class="title is-6 mb-0">
                    {i18n("matches", t)} ({matchesData.matches.length})
                </h4>
            {/if}
        </div>
    {/snippet}
    <!-- @migration-task-ok: migrate this slot by hand, `right-scroll` is an invalid identifier -->
    {#snippet rightScroll()}
        <div slot="right-scroll">
            {#if matchesData.matches.length}
                <Matches matches={matchesData.matches} columns={matchesData.columns} pairCat={$pairCat} {clusterStore}/>
            {:else}
                <p class="has-text-grey is-size-7">{i18n("selectImage", t)}</p>
            {/if}
        </div>
    {/snippet}
</SplitLayout>

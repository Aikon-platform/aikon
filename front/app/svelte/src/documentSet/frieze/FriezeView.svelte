<script>
    import { writable } from "svelte/store";
    import { i18n } from "../../utils.js";
    import SplitLayout from "../../ui/SplitLayout.svelte";
    import SpatialFrieze from "./SpatialFrieze.svelte";
    import Matches from "../Matches.svelte";

    export let documentSetStore;

    const {
        documentNodes, sortedDocumentNodes, visiblePairs, buildFriezeMatches, buildClusterMatches
    } = documentSetStore;

    const friezeStub = { nodeTitles: writable({}) };

    let friezeMode = "image";
    let selectedFriezeImage = null;
    let selectedCluster = null;

    $: documents = $sortedDocumentNodes.map(([, meta]) => meta);
    $: matchesData = selectedCluster
        ? buildClusterMatches(selectedCluster)
        : selectedFriezeImage
            ? buildFriezeMatches(selectedFriezeImage, $visiblePairs)
            : { matches: [], columns: [] };

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
    <div slot="left-title" class="is-flex is-justify-content-space-between is-align-items-center">
        <h4 class="title is-6 mb-0">{i18n("title", t)}</h4>
        <div class="select is-small">
            <select bind:value={friezeMode}>
                <option value="page">{i18n("byPage", t)}</option>
                <option value="image">{i18n("byImage", t)}</option>
            </select>
        </div>
    </div>
    <div slot="left-scroll">
        <SpatialFrieze
            {documents} {visiblePairs} {documentNodes}
            stemmaStore={friezeStub}
            mode={friezeMode}
            on:imageselect={handleImageSelect}
            on:clusterselect={handleClusterSelect}
        />
    </div>

    <div slot="right-title">
        {#if matchesData.matches.length}
            <h4 class="title is-6 mb-0">
                {i18n("matches", t)} ({matchesData.matches.length})
            </h4>
        {/if}
    </div>
    <div slot="right-scroll">
        {#if matchesData.matches.length}
            <Matches matches={matchesData.matches} columns={matchesData.columns}/>
        {:else}
            <p class="has-text-grey is-size-7">{i18n("selectImage", t)}</p>
        {/if}
    </div>
</SplitLayout>

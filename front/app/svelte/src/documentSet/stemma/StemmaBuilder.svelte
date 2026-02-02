<script>
    import { i18n } from '../../utils.js';
    import SplitLayout from '../../ui/SplitLayout.svelte';
    import StemmaVisualization from './StemmaVisualization.svelte';

    export let documentSetStore;

    const { documentNodes, filteredDocPairStats } = documentSetStore;

    const t = {
        title: { en: 'Stemma Builder', fr: 'Éditeur de stemma' },
        noDocuments: { en: 'No documents available', fr: 'Aucun document disponible' },
        details: { en: 'Details', fr: 'Détails' },
        selectNode: { en: 'Select a document node to view details', fr: 'Sélectionnez un document pour voir les détails' },
        edges: { en: 'Connections', fr: 'Connexions' },
        noEdges: { en: 'No connections yet', fr: 'Aucune connexion' },
        from: { en: 'From', fr: 'De' },
        to: { en: 'To', fr: 'Vers' },
    };

    let stemmaViz;
    let selectedNode = null;
    let createdEdges = [];

    $: documents = Array.from($documentNodes?.values() || []);

    function handleNodeSelect(e) {
        selectedNode = e.detail;
    }

    function handleEdgeCreate(e) {
        const { source, target } = e.detail;
        const srcDoc = $documentNodes.get(source);
        const tgtDoc = $documentNodes.get(target);
        createdEdges = [...createdEdges, {
            source,
            target,
            sourceTitle: srcDoc?.title || source,
            targetTitle: tgtDoc?.title || target
        }];
    }

    function removeEdge(source, target) {
        createdEdges = createdEdges.filter(e => !(e.source === source && e.target === target));
        stemmaViz?.removeEdge(source, target);
    }
</script>

{#if !documents.length}
    <div class="container">
        <div class="notification is-info">{i18n('noDocuments', t)}</div>
    </div>
{:else}
    <SplitLayout>
        <div slot="left-title" class="is-flex is-justify-content-space-between is-align-items-center">
            <h4 class="title is-6 mb-0">{i18n('title', t)}</h4>
            <span class="tag is-light">{documents.length} documents</span>
        </div>
        <div slot="left-scroll" class="stemma-panel">
            <StemmaVisualization
                bind:this={stemmaViz}
                {documents}
                on:nodeselect={handleNodeSelect}
                on:edgecreate={handleEdgeCreate}
            />
        </div>
        <div slot="right-title">
            <h4 class="title is-6 mb-0">{i18n('details', t)}</h4>
        </div>
        <div slot="right-scroll">
            {#if selectedNode}
                <div class="box mb-4">
                    <h5 class="title is-6" style="color: {selectedNode.color}">{selectedNode.title}</h5>
                    <p class="is-size-7 has-text-grey">ID: {selectedNode.id}</p>
                </div>
            {:else}
                <p class="has-text-grey is-size-7">{i18n('selectNode', t)}</p>
            {/if}

            <h5 class="title is-6 mt-5">{i18n('edges', t)}</h5>
            {#if createdEdges.length === 0}
                <p class="has-text-grey is-size-7">{i18n('noEdges', t)}</p>
            {:else}
                <div class="edge-list">
                    {#each createdEdges as edge}
                        <div class="edge-item is-flex is-align-items-center is-justify-content-space-between mb-2">
                            <span class="is-size-7">
                                <strong>{edge.sourceTitle}</strong> → <strong>{edge.targetTitle}</strong>
                            </span>
                            <button class="delete is-small" on:click={() => removeEdge(edge.source, edge.target)}></button>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </SplitLayout>
{/if}

<style>
    .stemma-panel {
        height: 100%;
        min-height: 500px;
    }
    .edge-item {
        padding: 0.5rem;
        background: var(--bulma-background);
        border-radius: 4px;
    }
</style>

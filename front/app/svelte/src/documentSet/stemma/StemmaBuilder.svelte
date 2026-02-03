<script>
    import { i18n } from '../../utils.js';
    import SplitLayout from '../../ui/SplitLayout.svelte';
    import StemmaVisualization from './StemmaVisualization.svelte';
    import { createStemmaStore } from './stemmaStore.js';

    export let documentSetStore;

    const stemmaStore = createStemmaStore(documentSetStore);
    const { selectedNodes, edges, filteredDocuments } = stemmaStore;

    const t = {
        title: { en: 'Stemma Builder', fr: 'Éditeur de stemma' },
        hint: { en: 'Drag to move • Scroll to zoom • Shift+drag to connect', fr: 'Glisser pour déplacer • Défiler pour zoomer • Maj+glisser pour connecter' },
        noDocuments: { en: 'No documents available', fr: 'Aucun document disponible' },
        order: { en: 'Order', fr: 'Ordre' },
        edges: { en: 'Connections', fr: 'Connexions' },
        selectViz: { en: 'Select a visualization', fr: 'Choisir une visualisation' },
    };

    $: documentSetStore.updateSelectedNodes($selectedNodes.map(n => n.id));

    function handleEdgeCreate(e) {
        const { source, target } = e.detail;
        const srcDoc = $filteredDocuments.find(d => d.id === source);
        const tgtDoc = $filteredDocuments.find(d => d.id === target);
        stemmaStore.addEdge(source, target, srcDoc, tgtDoc);
    }

    function removeEdge(source, target) {
        stemmaStore.removeEdge(source, target);
    }
</script>

{#if !$filteredDocuments.length}
    <div class="container">
        <div class="notification is-info">{i18n('noDocuments', t)}</div>
    </div>
{:else}
    <SplitLayout>
        <div slot="left-title" class="is-flex is-justify-content-space-between is-align-items-center">
            <h4 class="title is-6 mb-0">{i18n('title', t)}</h4>
            <span class="tag is-small">{i18n('hint', t)}</span>
        </div>
        <div slot="left-scroll" class="stemma-panel">
            {#if $selectedNodes.length}
                <div class="selection-bar mb-2">
                    <span class="is-size-7 has-text-grey mr-2">{i18n('order', t)}:</span>
                    <div class="is-flex is-flex-wrap-wrap" style="gap: 0.25rem;">
                        {#each $selectedNodes as node, idx (node.id)}
                            <span class="tag is-small" style="background-color: {node.color}; color: #222;">
                                <span class="mr-1">{idx + 1}.</span>
                                {node.title.length > 12 ? node.title.slice(0, 10) + '…' : node.title}
                            </span>
                        {/each}
                    </div>
                </div>
            {/if}

            {#if $edges.length}
                <div class="edges-bar mb-2">
                    <span class="is-size-7 has-text-grey mr-2">{i18n('edges', t)}:</span>
                    <div class="is-flex is-flex-wrap-wrap" style="gap: 0.25rem;">
                        {#each $edges as edge}
                            <span class="tag is-small">
                                <span class="edge-dot" style="background: {edge.sourceColor}"></span>
                                →
                                <span class="edge-dot" style="background: {edge.targetColor}"></span>
                                <button class="delete is-small ml-1" on:click={() => removeEdge(edge.source, edge.target)}></button>
                            </span>
                        {/each}
                    </div>
                </div>
            {/if}

            <div class="canvas-wrapper">
                <StemmaVisualization
                    documents={$filteredDocuments}
                    selectedNodes={$selectedNodes}
                    edges={$edges}
                    on:edgecreate={handleEdgeCreate}
                />
            </div>
        </div>

        <div slot="right-title" class="is-flex is-align-items-center" style="gap: 0.5rem;">
            <div class="select is-small">
                <select>
                    <option value="">{i18n('selectViz', t)}</option>
                </select>
            </div>
            <div class="select is-small">
                <select>
                    <option value="">{i18n('selectViz', t)}</option>
                </select>
            </div>
        </div>

        <div slot="right-scroll">
        </div>
    </SplitLayout>
{/if}

<style>
    .stemma-panel {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .canvas-wrapper {
        flex: 1;
        min-height: 400px;
        position: relative;
    }
    .selection-bar, .edges-bar {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        padding: 0.5rem;
        background: var(--bulma-scheme-main-bis);
        border-radius: 4px;
    }
    .edge-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
    }
</style>

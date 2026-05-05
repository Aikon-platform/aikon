<script>
    import DocumentStemma from "./DocumentStemma.svelte";
    import { i18n } from "../../utils.js";

    export let stemmaStore;
    export let documents;
    export let selectedNodes;
    export let nodeTitles;

    const t = { order: { en: "Order", fr: "Ordre" } };
</script>

<div class="stemma-panel">
    {#if selectedNodes.length}
        <div class="selection-bar mb-2">
            <span class="is-size-7 has-text-grey mr-2">{i18n("order", t)}:</span>
            <div class="is-flex is-flex-wrap-wrap" style="gap: 0.25rem;">
                {#each selectedNodes as node, idx (node.id)}
                    {@const title = nodeTitles[node.id] || node.title}
                    <span class="tag is-small" style="background-color: {node.color}; color: #222;">
                        <span class="mr-1">{idx + 1}.</span>
                        {title.length > 12 ? title.slice(0, 10) + "…" : title}
                    </span>
                {/each}
            </div>
        </div>
    {/if}
    <div class="canvas-wrapper">
        <DocumentStemma {documents} {stemmaStore}/>
    </div>
</div>

<style>
    .stemma-panel { display: flex; flex-direction: column; height: 100%; }
    .canvas-wrapper { flex: 1; min-height: 400px; position: relative; }
    .selection-bar {
        display: flex; align-items: center; flex-wrap: wrap;
        padding: 0.5rem; background: var(--bulma-scheme-main-bis); border-radius: 4px;
    }
</style>

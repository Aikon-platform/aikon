<script>
    import { preventDefault } from 'svelte/legacy';

    import Table from "../../Table.svelte";
    import Row from "../../Row.svelte";
    import Toolbar from "../../Toolbar.svelte";
    import {appLang} from "../../constants.js";
    import { categoryInfo } from "../../regions/similarity/similarityCategory.js";
    import Pagination from "../../Pagination.svelte";
    import RegionsSelectionModal from "../../regions/RegionsSelectionModal.svelte";
    import { clusterSelection } from "../../selection/selectionStore.js";
    import Regions from "../../regions/Regions.svelte";

    let { documentSetStore, clusterStore } = $props();
    const { imageNodes, selectedCategories } = documentSetStore;
    const {
        clusterNb,
        paginatedClusters,
        pageLength,
        validateCluster,
        newCluster,
        categorizeSelection,
        removeFromClusters
    } = clusterStore;

    const actionLabels = {
        create: {
            title: appLang === "en" ? "New cluster" : "Nouveau cluster",
            desc: appLang === "en" ? "Create a new validated cluster from the selected regions" : "Créer un nouveau cluster valide à partir des régions sélectionnées",
            icon: "fa-object-group",
            shortcut: "Shift + C",
            fct: newCluster
        },
        remove: {
            title: appLang === "en" ? "Remove from cluster" : "Retirer du cluster",
            desc: appLang === "en" ? "Remove the selected regions from their cluster" : "Retirer les régions sélectionnées de leur cluster",
            icon: "fa-chain-broken",
            shortcut: "Shift + D",
            fct: removeFromClusters
        },
        // delete: {
        //     title: appLang === 'en' ? 'Delete regions' : 'Supprimer les régions',
        //     desc: appLang === 'en' ? 'Remove selected regions from the document' : 'Supprimer du document les régions sélectionnées',
        //     icon: 'fa-trash',
        //     shortcut: 'Shift + X',
        //     fct: () => window.alert("Delete regions function not implemented yet.");
        // },
        validate: {
            title: appLang === "en" ? "Validate cluster" : "Valider le cluster",
            desc: appLang === "en" ? "Set as exact match all the pairs of regions in the cluster" : "Définir comme correspondance exacte toutes les paires de régions dans le cluster",
            icon: "fa-check",
            fct: validateCluster
        },
        validated: {
            title: appLang === "en" ? "Validated cluster" : "Cluster valide",
            desc: appLang === "en" ? "All pairs of regions have be categorized as exact matches" : "Toutes les paires de régions ont été catégorisées comme des correspondances exactes",
            icon: "fa-check"
        }
    };

    const { validate, validated, ...globalActions } = actionLabels;

    let clusterItems = $derived(new Map(
        $paginatedClusters.map(cl => [
            cl.id,
            cl.members.map(imgId => ({...$imageNodes.get(imgId), clusterId: cl.id}))
        ])
    ));

    let onlyOneSelectedCategory = $derived($selectedCategories.length === 1);
    let onlyExactMatches = $derived($selectedCategories.length === 1 && $selectedCategories[0] === 1);
</script>

<Toolbar expandable={false}>
    <!-- @migration-task-ok: migrate this slot by hand, `toolbar-visible` is an invalid identifier -->
    <!-- <div slot="toolbar-visible"> -->
    {#snippet toolbarVisible()}
        <div class="columns is-vcentered is-mobile py-4">
            <div class="field has-addons">
                <p class="control">
                     <button class="button is-link is-selected has-text-light is-unclickable">
                         {appLang === "en" ? "Categorize selection as" : "Catégoriser la sélection comme"}
                     </button>
                </p>
                <p class="control">
                    <button class="button py-3"
                            onclick={(e) => { e.preventDefault(); onlyExactMatches ? newCluster() : categorizeSelection(1); }}
                            title={onlyExactMatches ? actionLabels.create.title : categoryInfo[1].action}>
                        {@html categoryInfo[1].svg}
                    </button>
                </p>
                {#each [2, 3] as cat}
                    <p class="control">
                        <button class="button py-3" onclick={(e) => { e.preventDefault(); categorizeSelection(cat) }}
                                title={categoryInfo[cat].action}>
                            {@html categoryInfo[cat].svg}
                        </button>
                    </p>
                {/each}
                {#if onlyOneSelectedCategory}
                    <!-- Skip "remove" action if more than one category is selected -->
                    <!-- Because it makes no sense to uncategorize pairs that have different or no category -->
                    <p class="control">
                        <button class="button py-3" onclick={(e) => { e.preventDefault(); removeFromClusters()}}
                                title={actionLabels.remove.title}>
                            {@html categoryInfo[0].svg}
                        </button>
                    </p>
                {/if}
            </div>
        </div>
    {/snippet}
</Toolbar>

<Pagination store={clusterStore} nbOfItems={$clusterNb} {pageLength}/>

<RegionsSelectionModal selectionStore={clusterSelection}/>

<Table>
    {#each $paginatedClusters as cl (cl.id)}
        <Row>
            <!-- @migration-task-ok: migrate this slot by hand, `row-header` is an invalid identifier -->
            {#snippet rowHeader()}
                                <div class="cluster-info is-center is-fullwidth">
                    <span class="cluster-size">{cl.size} images</span>
                    <hr>
                    {#if !cl.fullyConnected}
                        <button class="button is-small is-warning" title={validate.desc} onclick={() => validate.fct(cl)}>
                            {validate.title}
                        </button>
                    {:else}
                        <span class="button is-small is-success" title={validated.desc}>
                            {validated.title}
                        </span>
                    {/if}
                </div>
            {/snippet}
            <!-- @migration-task-ok: migrate this slot by hand, `row-body` is an invalid identifier -->
            {#snippet rowBody()}
                <Regions items={clusterItems.get(cl.id)} copyable={true} selectionStore={clusterSelection}/>
            {/snippet}
        </Row>
    {/each}
</Table>

<Pagination store={clusterStore} nbOfItems={$clusterNb} {pageLength}/>

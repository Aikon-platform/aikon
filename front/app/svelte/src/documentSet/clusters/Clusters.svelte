<script>
    import Table from "../../Table.svelte";
    import Row from "../../Row.svelte";
    import Toolbar from "../../Toolbar.svelte";
    import {appLang, isSuperuser} from "../../constants.js";
    import Pagination from "../../Pagination.svelte";
    import RegionsSelectionModal from "../../regions/RegionsSelectionModal.svelte";
    import { clusterSelection } from '../../selection/selectionStore.js';
    import Regions from "../../regions/Regions.svelte";

    export let documentSetStore;
    const { imageNodes, selectedCategories } = documentSetStore;
    export let clusterStore;
    const {
        clusterNb,
        paginatedClusters,
        pageLength,
        validateCluster,
        newCluster,
        removeFromClusters
    } = clusterStore;

    // $: onlyPartial = true;
    // $: onlyNotValidated = true;

    const actionLabels = {
        create: {
            title: appLang === 'en' ? 'New cluster' : 'Nouveau cluster',
            desc: appLang === 'en' ? 'Create a new validated cluster from the selected regions' : 'Créer un nouveau cluster valide à partir des régions sélectionnées',
            icon: 'fa-object-group',
            shortcut: 'Shift + C',
            fct: newCluster
        },
        remove: {
            title: appLang === 'en' ? 'Remove from cluster' : 'Retirer du cluster',
            desc: appLang === 'en' ? 'Remove the selected regions from their cluster' : 'Retirer les régions sélectionnées de leur cluster',
            icon: 'fa-chain-broken',
            shortcut: 'Shift + D',
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
            title: appLang === 'en' ? 'Validate cluster' : 'Valider le cluster',
            desc: appLang === 'en' ? 'Set as exact match all the pairs of regions in the cluster' : 'Définir comme correspondance exacte toutes les paires de régions dans le cluster',
            icon: 'fa-check',
            fct: validateCluster
        },
        validated: {
            title: appLang === 'en' ? 'Validated cluster' : 'Cluster valide',
            desc: appLang === 'en' ? 'All pairs of regions have be categorized as exact matches' : 'Toutes les paires de régions ont été catégorisées comme des correspondances exactes',
            icon: 'fa-check'
        }
    };

    const { validate, validated, ...globalActions } = actionLabels;

    $: clusterItems = new Map(
        $paginatedClusters.map(cl => [
            cl.id,
            cl.members.map(imgId => ({...$imageNodes.get(imgId), clusterId: cl.id}))
        ])
    );

    $: onlyExactMatches = $selectedCategories.length === 1 && $selectedCategories[0] === 1;
</script>

{#if isSuperuser}
<Toolbar expandable={false}>
    <div slot="toolbar-visible">
        <div class="columns is-vcentered is-mobile py-4">
            <div class="column is-narrow mr-5">
                <span class="tag is-medium is-link mr-5">
                    {appLang === "en" ? "Process selection" : "Agir sur la sélection"}
                </span>
            </div>
            <div class="column">
                <div class="field has-addons">
                    {#each Object.values(globalActions) as action}
                        {#if !onlyExactMatches && action.title === actionLabels.remove.title}
                            <!-- Skip "remove" action if other category are selected -->
                            <!-- Because it makes no sense to remove the category "exact match" from pairs that do not have it -->
                        {:else}
                            <p class="control">
                                <button class="button pl-5" on:click|preventDefault={action.fct} title={action.desc}>
                                    <span class="icon is-small">
                                        <i class="fas {action.icon}"/>
                                    </span>
                                    {action.title}
                                    <span class="shortcut">{action.shortcut}</span>
                                </button>
                            </p>
                        {/if}
                    {/each}
                </div>
            </div>
        </div>
    </div>
</Toolbar>
{/if}

<Pagination store={clusterStore} nbOfItems={$clusterNb} {pageLength}/>

<RegionsSelectionModal selectionStore={clusterSelection}/>

<Table>
    {#each $paginatedClusters as cl (cl.id)}
        <Row>
            <svelte:fragment slot="row-header">
                <div class="cluster-info is-center is-fullwidth">
                    <span class="cluster-size">{cl.size} images</span>
                    <hr>
                    {#if !cl.fullyConnected}
                        <button class="button is-small is-warning" title={validate.desc} on:click={() => validate.fct(cl)}>
                            {validate.title}
                        </button>
                    {:else}
                        <span class="button is-small is-success" title={validated.desc}>
                            {validated.title}
                        </span>
                    {/if}
                </div>
            </svelte:fragment>
            <svelte:fragment slot="row-body">
                <Regions items={clusterItems.get(cl.id)} copyable={false} selectionStore={clusterSelection}/>
            </svelte:fragment>
        </Row>
    {/each}
</Table>

<Pagination store={clusterStore} nbOfItems={$clusterNb} {pageLength}/>

<style>
    .shortcut {
        display: none;
        font-family: monospace;
        font-size: 0.85em;
        font-weight: bold;
        color: var(--bulma-text-light-color);
        margin-left: 0.5em;
        padding: 0.2em 0.4em;
        background-color: var(--contrasted);
    }
</style>

<script>
    import Region from "../regions/Region.svelte";
    import Table from "../Table.svelte";
    import Row from "../Row.svelte";
    import Toolbar from "../Toolbar.svelte";
    import {appLang, appName, csrfToken} from "../constants.js";
    import {withLoading} from "../utils.js";
    import Pagination from "../Pagination.svelte";
    import RegionsSelectionModal from "../regions/RegionsSelectionModal.svelte";

    import { clusterSelection } from '../selection/selectionStore.js';
    export let documentSetStore;
    const {
        paginatedClusters,
        imageNodes,
        imageClusters,
        pageLength,
        clusterValidation
    } = documentSetStore;

    const fonction = () => console.log("prout");

    const imgRef2pairInfo = (imgRef) => {
        const [regionId, ...rest] = imgRef.split('_');
        return {img: rest.join('_'), regionId};
    };

    const pairwise = (arr) => {
        const pairs = [];
        for (let i = 0; i < arr.length; i++) {
            for (let j = i + 1; j < arr.length; j++) {
                pairs.push([arr[i], arr[j]]);
            }
        }
        return pairs;
    };

    const validateCluster = async (cluster) => {
        const pairs = pairwise(cluster.members).map(([ref1, ref2]) => {
            const {img: img1, regionId: reg1} = imgRef2pairInfo(ref1);
            const {img: img2, regionId: reg2} = imgRef2pairInfo(ref2);
            return {img_1: img1, img_2: img2, regions_id_1: reg1, regions_id_2: reg2};
        });

        try {
            const response = await withLoading(() => fetch(`${window.location.origin}/${appName}/exact-match-batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({pairs})
            }));

            if (!response.ok) {
                console.error('Batch validation failed');
                return false;
            }

            const res = await response.json();
            console.log(res);
            clusterValidation(cluster.id)

            return true;
        } catch (error) {
            console.error('Error:', error);
            return false;
        }
    };

    $: onlyPartial = true;
    $: onlyNotValidated = true;

    const actionLabels = {
        create: {
            title: appLang === 'en' ? 'New cluster' : 'Nouveau cluster',
            desc: appLang === 'en' ? 'Create a new validated cluster from the selected regions' : 'Créer un nouveau cluster valide à partir des régions sélectionnées',
            icon: 'fa-object-group',
            shortcut: 'Shift + C',
            fct: fonction
        },
        remove: {
            title: appLang === 'en' ? 'Remove from cluster' : 'Retirer du cluster',
            desc: appLang === 'en' ? 'Remove the selected regions from their cluster' : 'Retirer les régions sélectionnées de leur cluster',
            icon: 'fa-chain-broken',
            shortcut: 'Shift + D',
            fct: fonction
        },
        delete: {
            title: appLang === 'en' ? 'Delete regions' : 'Supprimer les régions',
            desc: appLang === 'en' ? 'Remove selected regions from the document' : 'Supprimer du document les régions sélectionnées',
            icon: 'fa-trash',
            shortcut: 'Shift + X',
            fct: fonction
        },
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
</script>



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
                        <p class="control">
                            <button class="button pl-5" on:click|preventDefault={action.fct} title={action.desc}>
                                <span class="icon is-small"><i class="fas {action.icon}"/></span>
                                {action.title}
                                <span class="shortcut">{action.shortcut}</span>
                            </button>
                        </p>
                    {/each}
                </div>
            </div>
        </div>
    </div>
</Toolbar>

<Pagination store={documentSetStore} nbOfItems={$imageClusters.length} {pageLength}/>

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
                {#each cl.members as imgId}
                    <Region item={$imageNodes.get(imgId)} copyable={false} selectionStore={clusterSelection}/>
                {/each}
            </svelte:fragment>
        </Row>
    {/each}
</Table>

<Pagination store={documentSetStore} nbOfItems={$imageClusters.length} {pageLength}/>

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

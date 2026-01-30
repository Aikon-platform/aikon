<script>
    import {appLang, model2title} from '../../constants.js';
    import CategoryButton from "../../regions/similarity/CategoryButton.svelte";
    import { activeLayout } from '../../ui/tabStore.js';
    import {getContext} from "svelte";
    import Legend from "./Legend.svelte";
    import InputSlider from "../../ui/InputSlider.svelte";

    export let docSet = null;
    export let documentSetStore;
    export let clusterStore;
    const {
        docSetNumber,
        documentNodes,
        selectedCategories,
        toggleCategory,
        selectedRegions,
        selectAllRegions,
        toggleRegion,
        threshold,
        setThreshold,
        topK,
        setTopK,
        mutualTopK,
        setMutualTopK,
        scoreMode,
        setScoreMode,
        pairStats,
        scoreFilter,
        setScoreFilter,
    } = documentSetStore;
    const { clusterNb, handlePageUpdate } = clusterStore;

    const selectedDocuments = getContext('selectedDocuments');

    const allCategories = [0, 1, 2, 3, 5];
    let filterMode = 'filtered';

    function setFilterMode(mode) {
        filterMode = mode;
        if (mode === 'all' && $selectedCategories.length !== allCategories.length) {
            selectedCategories.set(allCategories);
        }
    }
    function handleSetScoreMode(mode){
        handlePageUpdate(1);
        setScoreMode(mode)
    }
</script>

<div class="m-4 py-5 px-4">
    {#if $docSetNumber}
        <div class="content is-small mt-4">
            <div class="pb-2">
                <h1 class="title">
                    {docSet?.title}
                </h1>
                <div class="level">
                    {#each ['Series', 'Witness', 'Work'] as model}
                        {@const modelIds = Object.keys(selectedDocuments[model] || {})}
                        {#if modelIds.length > 0}
                            <div class="level-item has-text-centered">
                                <div>
                                    <p class="heading">{model2title[model]}</p>
                                    <p class="title is-5">{modelIds.length || 0}</p>
                                </div>
                            </div>
                        {/if}
                    {/each}

                    <div class="level-item has-text-centered">
                        <div>
                            <p class="heading">{appLang === 'en' ? 'Pairs' : 'Paires'}</p>
                            <p class="title is-5">{$docSetNumber.pairs || 0}</p>
                        </div>
                    </div>
                    <div class="level-item has-text-centered">
                        <div>
                            <p class="heading">Images</p>
                            <p class="title is-5">{$docSetNumber.images || 0}</p>
                        </div>
                    </div>
                    <div class="level-item has-text-centered">
                        <div>
                            <p class="heading">Clusters</p>
                            <p class="title is-5">{$clusterNb || 0}</p>
                        </div>
                    </div>
                </div>
            </div>

            <hr>

            <Legend documentNodes={$documentNodes} selectedRegions={$selectedRegions} {toggleRegion} {selectAllRegions}/>

            <hr>

            <div class="pt-2">
                <h3 class="title">
                    {appLang === 'en' ? 'Similarity categories' : 'Catégories de similarité'}
                </h3>
                <div class="buttons mb-3">
                    {#each ['all', 'filtered'] as mode}
                        <button class="button is-small is-flex-grow-1"
                            class:is-link={filterMode === mode}
                            class:is-contrasted={filterMode !== mode}
                            on:click={() => setFilterMode(mode)}>
                            {
                                mode === 'all' ?
                                appLang === 'en' ? 'All pairs' : 'Toutes les paires' :
                                appLang === 'en' ? 'Filter by category' : 'Filtrer par catégorie'
                            }
                        </button>
                    {/each}
                </div>

                <div class="level" class:is-disabled={filterMode === 'all'}>
                    {#each allCategories as cat}
                        <div class="level-item has-text-centered">
                            <div>
                                <CategoryButton
                                    category={cat}
                                    isSelected={$selectedCategories.includes(cat)}
                                    toggle={(cat) => filterMode === 'filtered' ? toggleCategory(cat) : null}
                                    selectable={filterMode === 'filtered'}/>
                                <p class="is-size-7 mt-1">{$docSetNumber.categories[cat] || 0}</p>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <hr>

            <div class="pt-2">
                <div class="level is-mobile">
                    <div class="level-left">
                        <div class="level-item">
                            <h3 class="title">
                                {appLang === 'en' ? 'Similarity score' : 'Score de similarité'}
                            </h3>
                        </div>
                    </div>
                    <div class="level-right">
                        <div class="level-item">
                            <label class="checkbox mt-1 is-flex is-align-items-center">
                                <input on:change={() => setScoreFilter(!$scoreFilter)} checked={!$scoreFilter} type="checkbox" class="mr-2"/>
                                <span class="is-size-7">
                                    {appLang === 'en' ? 'Disable filtering' : 'Désactiver le filtrage'}
                                </span>
                            </label>
                        </div>
                    </div>
                </div>

                <div class:disabled={!$scoreFilter}>
                    <div class="buttons mb-3">
                        {#each ['threshold', 'topk'] as mode}
                            <button class="button is-small is-flex-grow-1"
                                    class:is-link={$scoreMode === mode}
                                    class:is-contrasted={$scoreMode !== mode}
                                    on:click={() => handleSetScoreMode(mode)}>
                                {
                                    mode === 'threshold' ?
                                        appLang === 'en' ? 'Score threshold' : 'Seuil de score' :
                                        appLang === 'en' ? 'Top K pairs' : 'Top K paires'
                                }
                            </button>
                        {/each}
                    </div>

                    {#if $scoreMode === 'threshold'}
                        <InputSlider minVal={$pairStats.scoreRange?.min || 0} maxVal={$pairStats.scoreRange?.max || 500}
                                     start={$threshold} step={0.01} roundTo={1}
                                     title={appLang === 'en' ? 'Minimum score' : 'Score minimum'}
                                     on:updateSlider={(e) => setThreshold(e.detail)}/>
                    {:else}
                        <div class="columns mt-2">
                            <div class="column is-two-thirds pl-4">
                                <InputSlider minVal={1} maxVal={5} start={$topK} step={1} roundTo={0} title="K"
                                             on:updateSlider={(e) => setTopK(e.detail)}/>
                            </div>
                            <div class="column mt-2">
                                <label class="checkbox mt-3 is-flex is-align-items-center">
                                    <input on:change={() => setMutualTopK(!$mutualTopK)} checked={$mutualTopK}
                                           type="checkbox" class="mr-2"/>
                                    <span class="is-size-7">
                                        {appLang === 'en' ? 'Mutual top K' : 'Top K mutuel'}
                                    </span>
                                </label>
                            </div>
                        </div>
                    {/if}
                </div>
            </div>

            <hr>

            <div class="py-2">
                <h3 class="title">
                    {appLang === 'en' ? 'Visualisation information' : 'Informations sur la visualisation'}
                </h3>
                {#if $activeLayout === "img"}
                    <p>
                        {appLang === 'en'
                            ? 'Network where each node is an image region. Edges connect regions with similarity scores above the threshold. Node color indicates the source document.'
                            : 'Réseau où chaque nœud est une région d\'image. Les liens connectent les régions dont le score de similarité dépasse le seuil. La couleur indique le document source.'}
                    </p>
                {:else if $activeLayout === "doc"}
                    <p>
                        {appLang === 'en'
                            ? 'Network where each node is a document. Edge thickness reflects the cumulative similarity score between document pairs. Node size indicates the number of connections.'
                            : 'Réseau où chaque nœud est un document. L\'épaisseur des liens reflète le score de similarité cumulé entre paires de documents. La taille des nœuds indique le nombre de connexions.'}
                    </p>
                {:else if $activeLayout === "mat"}
                    <p>
                        {appLang === 'en'
                            ? 'Matrix showing aggregated similarity scores between documents. Click a cell to explore page-level similarities in a scatter plot interface.'
                            : 'Matrice affichant les scores de similarité agrégés entre documents. Cliquez sur une cellule pour explorer les similarités entre paires de documents.'}
                    </p>
                {:else if $activeLayout === "sim"}
                    <p>
                        {appLang === 'en'
                            ? 'Groups of images that share a similarity connection above the score threshold.'
                            : 'Groupes d\'images partageant une connexion de similarité au-dessus du seuil de score.'}
                    </p>
                {/if}
                <!--<NetworkInfo/>-->
            </div>
        </div>
    {/if}
</div>

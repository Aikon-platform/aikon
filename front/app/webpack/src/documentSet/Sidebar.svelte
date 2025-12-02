<script>
    import {appLang, appUrl, appName, model2title} from '../constants.js';
    import CategoryButton from "../regions/similarity/CategoryButton.svelte";
    import LegendItem from "./LegendItem.svelte";
    import {getContext} from "svelte";

    export let docSet = null;
    export let documentSetStore;
    const {
        docSetNumber,
        documentNodes,
        imageClusters,
        selectedCategories,
        toggleCategory,
        selectedRegions,
        toggleRegion
    } = documentSetStore;

    const selectedDocuments = getContext('selectedDocuments');
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
                            <p class="title is-5">{$imageClusters.length || 0}</p>
                        </div>
                    </div>
                </div>

                <div class="legend-list">
                    {#each Array.from($documentNodes || new Map()) as [id, meta]}
                        <LegendItem id={id} meta={meta} isActive={$selectedRegions.has(parseInt(id))}
                                    toggle={() => toggleRegion(parseInt(id))}/>
                    {/each}
                </div>
            </div>

            <hr>

            <div class="pt-2">
                <h3 class="title">
                    {appLang === 'en' ? 'Similarity categories' : 'Catégories de similarité'}
                </h3>
                <div class="tags">
                    {#each [0, 1, 2, 3, 5] as cat}
                        <CategoryButton
                            category={cat}
                            isSelected={$selectedCategories.includes(cat)}
                            toggle={toggleCategory}
                        />
                        {$docSetNumber.categories[cat] || 0}
                    {/each}
                </div>
            </div>

            <hr>

            <div class="py-2">
                <h3 class="title">
                    {appLang === 'en' ? 'Visualisation information' : 'Informations sur la visualisation'}
                </h3>
                <slot name="datavizInfo"/>
            </div>
        </div>
    {/if}
</div>

<style>
    .legend-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
</style>

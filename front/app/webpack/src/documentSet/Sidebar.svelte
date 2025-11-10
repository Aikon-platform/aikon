<script>
    import {appLang, appUrl, appName, model2title} from '../constants.js';
    import CategoryButton from "../regions/similarity/CategoryButton.svelte";
    import LegendItem from "./LegendItem.svelte";

    export let docSet = null;
    export let documentSetStore;
    const {
        docSetStats,
        regionsMetadata,
        selectedCategories,
        toggleCategory,
        activeRegions,
        toggleRegion
    } = documentSetStore;
</script>

<div class="m-4 py-5 px-4">
    {#if $docSetStats}
        <div class="content is-small mt-4">
            <div class="pb-2">
                <h1 class="title">
                    {docSet?.title}
                </h1>
                <div class="level">
                    <div class="level-item has-text-centered">
                        <div>
                            <p class="heading">{model2title['Witness']}</p>
                            <p class="title is-5">{$docSetStats.witnesses}</p>
                        </div>
                    </div>
                    <div class="level-item has-text-centered">
                        <div>
                            <p class="heading">{appLang === 'en' ? 'Pairs' : 'Paires'}</p>
                            <p class="title is-5">{$docSetStats.pairs}</p>
                        </div>
                    </div>
                    <div class="level-item has-text-centered">
                        <div>
                            <p class="heading">Images</p>
                            <p class="title is-5">{$docSetStats.stats[0].nodes}</p>
                        </div>
                    </div>
                </div>

                <div class="legend-list">
                    {#each Object.entries($regionsMetadata || {}) as [id, meta]}
                        <LegendItem id={id} meta={meta} isActive={$activeRegions.has(parseInt(id))}
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
                        {$docSetStats.categories[cat] || 0}
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

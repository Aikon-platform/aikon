<script>
    import {appLang, appUrl, appName, model2title} from '../constants.js';
    import CategoryButton from "../regions/similarity/CategoryButton.svelte";

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

    console.log(docSetStats, docSet, $regionsMetadata);
    $: regionsList = regionsMetadata ? Object.entries($regionsMetadata) : [];
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
                    {#each regionsList as [id, meta]}
                        {@const regionId = parseInt(id)}
                        {@const isActive = $activeRegions.has(regionId)}
                        <div class="legend-item" class:inactive={!isActive}>
                            <span class="legend-nb"><!--IMAGE NUMBER--></span>
                            <span class="legend-color clickable" class:inactive={!isActive}
                                style="background-color: {isActive ? meta.color : '#999'};"
                                on:click={() => toggleRegion(regionId)} on:keydown={null}
                                role="button" tabindex="0" aria-label="Toggle region {meta.title}"/>
                            <span class="legend-label">
                                <a href={`${appUrl}/${appName}/witness/${meta.witnessId}/regions/${id}`} target="_blank">
                                    {meta.title}
                                </a>
                            </span>
                        </div>
                    {/each}
                </div>
            </div>

            <hr>

            <div class="pt-2">
                <h3 class="title">
                    {appLang === 'en' ? 'Similarity categories' : 'Catégories de similarité'}
                </h3>
                <div class="tags">
                    {#each [0, 1, 2, 3, 4, 5] as cat}
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

    .legend-nb {
        /* ADD  STYLE */
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.25rem 0;
        transition: opacity 0.2s;
    }

    .legend-item.inactive {
        opacity: 0.5;
    }

    .legend-color {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
        flex-shrink: 0;
        transition: all 0.2s;
    }

    .legend-color.clickable {
        cursor: pointer;
    }

    .legend-color.clickable:hover {
        transform: scale(1.2);
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.4);
    }

    .legend-color.inactive {
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }
</style>

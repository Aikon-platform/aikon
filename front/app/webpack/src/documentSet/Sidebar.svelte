<script>
    import {appLang, appUrl, appName, model2title} from '../constants.js';
    import CategoryButton from "../regions/similarity/CategoryButton.svelte";

    export let docSetStats = null;
    export let regionsMetadata = null;
    export let docSet = null;

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
                </div>

                <div class="legend-list">
                    {#each regionsList as [id, meta]}
                        <div class="legend-item">
                            <span class="legend-color" style="background-color: {meta.color};"></span>
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

            <div class="py-2">
                <h3 class="title">
                    {appLang === 'en' ? 'Visualisation information' : 'Informations sur la visualisation'}
                </h3>
                <slot name="datavizInfo"/>
            </div>

            <hr>

            <div class="pt-2">
                <h3 class="title">
                    {appLang === 'en' ? 'Similarity categories' : 'Catégories de similarité'}
                </h3>
                <div class="tags">
                    <CategoryButton category={parseInt(1)}/> {$docSetStats.categories[1] || 0}<br>
                    <CategoryButton category={parseInt(2)}/> {$docSetStats.categories[2] || 0}<br>
                    <CategoryButton category={parseInt(3)}/> {$docSetStats.categories[3] || 0}<br>
                    <CategoryButton category={parseInt(4)}/> {$docSetStats.categories[4] || 0}<br>
                    <CategoryButton category={parseInt(5)}/> {$docSetStats.categories[5] || 0}<br>
                </div>
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

    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.25rem 0;
    }

    .legend-color {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
        flex-shrink: 0;
    }
</style>

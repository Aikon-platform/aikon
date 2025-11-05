<script>
    import {appLang, model2title} from '../constants.js';
    import CategoryButton from "../regions/similarity/CategoryButton.svelte";
    export let docSetStats = null;
    export let regionsMetadata = null;
    export let docSet = null;

    console.log(docSetStats, docSet, $regionsMetadata);
    $: regionsList = regionsMetadata ? Object.entries($regionsMetadata) : [];
</script>

<div class="m-4">
    <h2 class="title is-5">{docSet?.name}</h2>

    {#if $docSetStats}
        <div class="content is-small mt-4">
            <div class="box">
                <p class="heading">Corpus overview</p>
                <div class="level is-mobile">
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
            </div>

            <div class="box">
                <p class="heading">Network metrics</p>
                <table class="table is-narrow is-fullwidth is-size-7">
                    <thead>
                        <tr>
                            <th></th>
                            <th class="has-text-centered">Nodes</th>
                            <th class="has-text-centered">Links</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Image network</td>
                            <td class="has-text-centered">{$docSetStats.imageNodes}</td>
                            <td class="has-text-centered">{$docSetStats.imageLinks}</td>
                        </tr>
                        <tr>
                            <td>Document network</td>
                            <td class="has-text-centered">{$docSetStats.docNodes}</td>
                            <td class="has-text-centered">{$docSetStats.docLinks}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!--{#if $docSetStats.avgScore}-->
            <!--    <div class="notification is-light is-info is-size-7">-->
            <!--        <strong>Average score:</strong> {$docSetStats.avgScore}-->
            <!--    </div>-->
            <!--{/if}-->

            {#if Object.keys($docSetStats.categories).length > 0}
                <div class="box">
                    <p class="heading">Categories</p>
                    <div class="tags">
                        {#each Object.entries($docSetStats.categories) as [cat, count]}
                            <CategoryButton category={parseInt(cat)}/> {count}
                        {/each}
                    </div>
                </div>
            {/if}
        </div>

        <div class="content is-small">
            <p class="heading">{appLang === 'en' ? 'Region Extractions' : 'Extraction de régions'}</p>
            <div class="menu">
                {#each regionsList as [id, meta]}
                    <a href={meta.url} target="_blank" class="menu-item"
                       style="border-left: 5px solid {meta.color};">
                        <span class="is-size-7">{meta.title}</span>
                    </a>
                {/each}
            </div>
        </div>
    {/if}

    <div id="legend"></div>
</div>

<style>
    .menu-item {
        display: block;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.25rem;
        border-radius: 4px;
        transition: background-color 0.15s;
    }
    .menu-item:hover {
        background-color: hsl(0, 0%, 96%);
    }
</style>

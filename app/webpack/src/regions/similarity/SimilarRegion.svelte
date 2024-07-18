<script>
    import { fade } from 'svelte/transition';
    import { refToIIIF } from "../../utils.js";
    import { similarityStore } from './similarityStore.js';
    import { userId, appLang, csrfToken } from '../../constants';
    import { exactSvg, partialSvg, semanticSvg, noSvg, userSvg } from './similarityCategory';

    const baseUrl = window.location.origin;

    export let qImg;
    export let sImg;
    export let score = 0;
    // export let qRegions = null;
    // export let sRegions = null;
    export let category = null;
    export let users = [];

    const [wit, digit, canvas, xyhw] = sImg.split('.')[0].split('_');
    const img = `${wit}_${digit}_${canvas}`;

    $: selectedCategory = category;
    $: isSelectedByUser = users.includes(Number(userId)) || false;

    function updateCategory(category) {
        if (category === 5) {
            isSelectedByUser = !isSelectedByUser;
        } else {
            selectedCategory = selectedCategory === category ? null : category;
        }
    }

    async function categorize(category) {
        updateCategory(category);

        try {
            const response = await fetch(`${baseUrl}/save-category`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    'img_1': qImg,
                    'img_2': sImg,
                    'category': selectedCategory,
                    'user_selected': isSelectedByUser,
                })
            });

            if (!response.ok) {
                console.error(`Error: Network response was not ok`);
                updateCategory(category);
            }

            // const data = await response.json();
        } catch (error) {
            console.error('Error:', error);
            updateCategory(category);
        }
    }
</script>

<div class="region is-center" transition:fade={{ duration: 500 }}>
    <figure class="image region-image card" tabindex="-1">
        <img src="{refToIIIF(img, xyhw, ',256')}" alt="Similar region"/>
        <div class="overlay is-center">
            <span class="overlay-desc">
                {similarityStore.getRegionsInfo(`${wit}_${digit}`).title}
                <br>
                Page {parseInt(canvas)}
                <br>
                <b>
                    {#if score}
                        Score: {score}
                    {:else}
                        {appLang === 'en' ? 'Manual similarity' : 'Correspondance manuelle'}
                    {/if}
                </b>
            </span>
        </div>
    </figure>
    <div class="tags has-addons is-dark is-center">
        <span class="tag is-hoverable pl-5 pr-4 py-4" class:is-link={selectedCategory === 1}
              on:click={() => categorize(1)} on:keyup={null}
              title="{appLang === 'en' ? 'Exact match' : 'Correspondance exacte'}">
            {@html exactSvg}
        </span>
        <span class="tag is-hoverable p-4" class:is-link={selectedCategory === 2}
              on:click={() => categorize(2)} on:keyup={null}
              title="{appLang === 'en' ? 'Partial match' : 'Correspondance partielle'}">
            {@html partialSvg}
        </span>
        <span class="tag is-hoverable p-4" class:is-link={selectedCategory === 3}
              on:click={() => categorize(3)} on:keyup={null}
              title="{appLang === 'en' ? 'Semantic match' : 'Correspondance sémantique'}">
            {@html semanticSvg}
        </span>
        <span class="tag is-hoverable p-4" class:is-link={selectedCategory === 4}
              on:click={() => categorize(4)} on:keyup={null}
              title="{appLang === 'en' ? 'No match' : 'Aucune correspondance'}">
            {@html noSvg}
        </span>
        <span class="tag is-hoverable pl-4 pr-5 py-4" class:is-link={isSelectedByUser}
              on:click={() => categorize(5)} on:keyup={null}
              title="{appLang === 'en' ? 'User match' : 'Correspondance utilisateur'}">
            {@html userSvg}
        </span>
    </div>
</div>

<style>
    .overlay {
        font-size: 75%;
    }
    figure {
        transition: outline 0.1s ease-out;
        outline: 0 solid var(--bulma-link);
    }
    .region {
        cursor: pointer;
        position: relative;
    }
    .region-image {
        height: 225px;
        display: flex;
        justify-content: center;
        align-items: center;
        overflow: hidden;
        position: relative;
        cursor: default;
    }
    .region-image img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        position: absolute;
    }
</style>

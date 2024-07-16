<script>
    import { fade } from 'svelte/transition';
    import { refToIIIF } from "../../utils.js";
    import { similarityStore } from './similarityStore.js';
    import { userId } from '../../constants';

    export let appLang = 'en';
    export let qImg;
    export let sImg;
    export let score;

    const baseUrl = window.location.origin;

    const [wit, digit, canvas, xyhw] = sImg.split('.')[0].split('_');
    const img = `${wit}_${digit}_${canvas}`;

    export let regionsCategory = null;

    $: selectedCategory = regionsCategory ? regionsCategory.category : null;
    $: isCategory5Selected = regionsCategory ? regionsCategory.category_x?.includes(Number(userId)) || false : false;

    function updateCategory(category) {
        if (category === 5) {
            isCategory5Selected = !isCategory5Selected;
        } else {
            selectedCategory = selectedCategory === category ? null : category;
        }
        // regionsCategory = {
        //     ...regionsCategory,
        //     category: selectedCategory,
        //     category_x: isCategory5Selected
        //         ? [...(regionsCategory.category_x || []), Number(userId)]
        //         : (regionsCategory.category_x || []).filter(id => id !== Number(userId))
        // };
    }

    async function categorize(category) {
        const [w1, d1, c1, _1] = qImg.split('.')[0].split('_');
        const [w2, d2, c2, _2] = sImg.split('.')[0].split('_');

        updateCategory(category);

        try {
            const response = await fetch(`${baseUrl}/save-category`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({
                    'img_1': qImg,
                    'img_2': sImg,
                    'regions_ref_1': `${w1}_${d1}_${c1}`, // TODO wrong regions ref
                    'regions_ref_2': `${w2}_${d2}_${c2}`,
                    'category': category <= 4 ? selectedCategory : null,
                    'category_x': category === 5 ? isCategory5Selected : null,
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
                <b>Score: {score}</b>
            </span>
        </div>
    </figure>
    <div class="tags has-addons is-dark is-center">
        <span class="tag is-hoverable pl-5 pr-4 py-4" class:is-link={selectedCategory === 1}
              on:click={() => categorize(1)} on:keyup={null}
              title="{appLang === 'en' ? 'Exact match' : 'Correspondance exacte'}">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 54 54.5">
                <rect x="30" y="30.62" width="55.71" height="55.71" rx="5.01" ry="5.01" fill="none" stroke="currentColor" stroke-width="3"/>
                <rect x="21" y="21" width="55.71" height="55.71" rx="5.01" ry="5.01" fill="none" stroke="currentColor" stroke-width="3"/>
                <rect x="30" y="30.62" width="46" height="45.71" rx="4.11" ry="4.11" fill="currentColor" stroke="none"/>
            </svg>
        </span>
        <span class="tag is-hoverable p-4" class:is-link={selectedCategory === 2}
              on:click={() => categorize(2)} on:keyup={null}
              title="{appLang === 'en' ? 'Partial match' : 'Correspondance partielle'}">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 55 55.5">
                <rect x="32" y="32.43" width="55.71" height="55.71" rx="5.01" ry="5.01" fill="none" stroke="currentColor" stroke-width="3" pointer-events="all"/>
                <rect x="21" y="20.81" width="55.71" height="55.71" rx="5.01" ry="5.01" fill="none" stroke="currentColor" stroke-width="3" pointer-events="all"/>
                <path d="M 32 41.43 L 41 32.43" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 32 50 L 50 32.43" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 60 76 L 77 58" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 68.3 76.29 L 77 67" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 32 59 L 59 32" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 32 68 L 68 32" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 33 76 L 77 32" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 51 76 L 77 49" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 41 77 L 77 41" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
            </svg>
        </span>
        <span class="tag is-hoverable p-4" class:is-link={selectedCategory === 3}
              on:click={() => categorize(3)} on:keyup={null}
              title="{appLang === 'en' ? 'Semantic match' : 'Correspondance sémantique'}">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 56.5">
                <rect x="34" y="34.43" width="55.71" height="55.71" rx="5.01" ry="5.01" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="9 9"/>
                <rect x="21" y="20.81" width="55.71" height="55.71" rx="5.01" ry="5.01" fill="none" stroke="currentColor" stroke-width="3"/>
            </svg>
        </span>
        <span class="tag is-hoverable p-4" class:is-link={selectedCategory === 4}
              on:click={() => categorize(4)} on:keyup={null}
              title="{appLang === 'en' ? 'No match' : 'Aucune correspondance'}">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 49.5 49.5">
                <rect x="21" y="20.62" width="55.71" height="55.71" rx="5.01" ry="5.01" fill="none" stroke="currentColor" stroke-width="3"/>
                <path d="M 22.67 74.55 L 75 22" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                <path d="M 74.37 74.05 L 22.72 22.24" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
            </svg>
        </span>
        <span class="tag is-hoverable pl-4 pr-5 py-4" class:is-link={isCategory5Selected}
              on:click={() => categorize(5)} on:keyup={null}
              title="{appLang === 'en' ? 'User match' : 'Correspondance utilisateur'}">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 49.5 49.5">
                <rect x="21" y="20.81" width="55.71" height="55.71" rx="5.01" ry="5.01" fill="none" stroke="currentColor" stroke-width="3"/>
                <path d="M 28.69 75.28 C 29.25 64.15 38.08 55.28 48.86 55.28 C 52.5 55.28 56.07 56.3 59.18 58.25 C 64.96 61.85 68.66 68.3 69.02 75.28 Z M 37.85 41.48 C 37.85 35.37 42.79 30.39 48.86 30.39 C 54.92 30.39 59.86 35.37 59.86 41.48 C 59.86 47.59 54.92 52.56 48.86 52.56 C 42.79 52.56 37.85 47.59 37.85 41.48 Z M 60.37 56.34 C 58.43 55.13 56.32 54.25 54.13 53.7 C 58.82 51.64 62.1 46.94 62.1 41.48 C 62.1 34.13 56.16 28.15 48.86 28.15 C 41.55 28.15 35.61 34.13 35.61 41.48 C 35.61 46.95 38.9 51.66 43.6 53.71 C 33.76 56.18 26.41 65.4 26.41 76.4 C 26.41 77.02 26.92 77.52 27.54 77.52 L 70.17 77.52 C 70.79 77.52 71.3 77.02 71.3 76.4 C 71.3 68.23 67.11 60.54 60.37 56.34 Z" fill="currentColor" stroke="none"/>
            </svg>
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
    svg {
        margin-top: -10px;
        margin-left: -10px;
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

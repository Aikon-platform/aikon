<script>
    import { similarityStore } from './similarityStore.js';
    import { userId, appLang, csrfToken, regionsType } from '../../constants';
    import { exactSvg, partialSvg, semanticSvg, noSvg, userSvg } from './similarityCategory';
    import Region from "../Region.svelte";

    const baseUrl = window.location.origin;

    export let qImg;
    export let sImg;
    export let score = 0;
    export let category = null;
    export let users = [];

    const [wit, digit, canvas, xyhw] = sImg.split('.')[0].split('_');

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
                // unselect category
                updateCategory(category);
            }
        } catch (error) {
            console.error('Error:', error);
            // unselect category
            updateCategory(category);
        }
    }

    const item = {
        id: sImg, // note for normal regions, it is their SAS annotation id: used for region selection
        img: sImg,
        xywh: xyhw,
        canvas: canvas,
        ref: sImg.replace('.jpg', ''),
        type: regionsType
    }

    const regionRef = `${wit}_${digit}`;
    const desc = `${similarityStore.getRegionsInfo(regionRef).title}<br>
        Page ${parseInt(canvas)}<br>
        <b>${score ? `Score: ${score}` : appLang === 'en' ? 'Manual similarity' : 'Correspondance manuelle'}</b>`
</script>

<div>
    <Region {item} size={256} {desc} isSquare={false}/>
    <div class="tags has-addons is-dark is-center">
        <span class="tag is-hoverable pl-4 pr-3 py-4" class:is-selected={selectedCategory === 1}
              on:click={() => categorize(1)} on:keyup={null}
              title="{appLang === 'en' ? 'Exact match' : 'Correspondance exacte'}">
            {@html exactSvg}
        </span>
        <span class="tag is-hoverable py-4 px-3" class:is-selected={selectedCategory === 2}
              on:click={() => categorize(2)} on:keyup={null}
              title="{appLang === 'en' ? 'Partial match' : 'Correspondance partielle'}">
            {@html partialSvg}
        </span>
        <span class="tag is-hoverable py-4 px-3" class:is-selected={selectedCategory === 3}
              on:click={() => categorize(3)} on:keyup={null}
              title="{appLang === 'en' ? 'Semantic match' : 'Correspondance sémantique'}">
            {@html semanticSvg}
        </span>
        <span class="tag is-hoverable py-4 px-3" class:is-selected={selectedCategory === 4}
              on:click={() => categorize(4)} on:keyup={null}
              title="{appLang === 'en' ? 'No match' : 'Aucune correspondance'}">
            {@html noSvg}
        </span>
        <span class="tag is-hoverable pl-3 pr-4 py-4" class:is-selected={isSelectedByUser}
              on:click={() => categorize(5)} on:keyup={null}
              title="{appLang === 'en' ? 'User match' : 'Correspondance utilisateur'}">
            {@html userSvg}
        </span>
    </div>
</div>

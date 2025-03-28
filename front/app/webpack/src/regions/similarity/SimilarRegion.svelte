<script>
    import { getContext } from "svelte";

    import { similarityStore } from './similarityStore.js';
    import { extractNb } from '../../utils.js';
    import { userId, appLang, csrfToken, regionsType, appName } from '../../constants';
    import { exactSvg, partialSvg, semanticSvg, noSvg, userSvg, validateSvg } from './similarityCategory';

    import Region from "../Region.svelte";
    import { derived } from "svelte/store";

    ////////////////////////////////////////////

    const windowUrl = new URL(window.location.href)
    const baseUrl = windowUrl.origin;
    const pathUrl = windowUrl.pathname;

    export let  qImg;
    export let  sImg;
    export let  qRegions;
    export let  sRegions;
    export let  score = 0;
    export let  category = null;
    export let  users = [];
    export let  isManual;

    const similarityPropagatedContext = getContext("similarityPropagatedContext") || false;  // true if it's a propagated match, false otherwise

    $: selectedCategory = category;
    $: isSelectedByUser = users.includes(Number(userId)) || false;

    ////////////////////////////////////////////

    const [wit, digit, canvas, xyhw] = sImg.split('.')[0].split('_');
    const item = {
        id: sImg, // note for normal regions, it is their SAS annotation id: used for region selection
        img: sImg,
        title: `Canvas ${canvas} - ${xyhw} - ${appLang === 'en' ? 'Witness' : 'Témoin'} #${extractNb(wit)}`,
        xywh: xyhw,
        canvas: canvas,
        ref: sImg.replace('.jpg', ''),
        type: regionsType
    }
    const regionRef = `${wit}_${digit}`;
    const desc = `${similarityStore.getRegionsInfo(regionRef).title}<br>
        Page ${parseInt(canvas)}<br>
        <b>${score ? `Score: ${score}` : appLang === 'en' ? 'Manual similarity' : 'Correspondance manuelle'}</b>`

    ////////////////////////////////////////////

    function updateCurrentUsers(_users) {
        _users = _users.slice();  // copy `_users`
        let userIndex = _users.indexOf(Number(userId));
        if ( isSelectedByUser && userIndex === -1  ) {
            _users.push(Number(userId));
        } else if ( !isSelectedByUser && userIndex !== -1 ) {
            _users.splice(userIndex, 1);
        }
        return _users;
    };

    const toRegionPair = () => ({
        img_1: qImg,
        img_2: sImg,
        regions_id_1: qRegions,
        regions_id_2: sRegions,
        score: score,
        category: selectedCategory,
        category_x: updateCurrentUsers(users),
        is_manual: isManual || similarityPropagatedContext
    })

    function updateCategory(category) {
        if (category === 5) {
            isSelectedByUser = !isSelectedByUser;
        } else {
            selectedCategory = selectedCategory === category ? null : category;
        }
    }

    ////////////////////////////////////////////

    /**
     * save the new RegionPair.category to database (RegionPair.category)
     * if `similarityPropagatedContext===true`, the whole RegionPair will be created
     * and saved to database: the current regionpair doesn't exist in database.
     */
    async function categorize(category) {
        console.log("categorize called !")
        updateCategory(category);
        console.log(toRegionPair());
        try {
            const response = await fetch(`${baseUrl}/${appName}/save-category`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(toRegionPair())
            });
            if (!response.ok) {
                console.error(`Error: Network response was not ok`);
                // unselect category
                updateCategory(category);
            } else {
                response.json().then(data => console.log("categorize success response", data))
            }
        } catch (error) {
            console.error('Error:', error);
            // unselect category
            updateCategory(category);
        }
    }
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

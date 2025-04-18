<script>
    import { getContext } from "svelte";

    import { similarityStore } from './similarityStore.js';
    import { extractNb } from '../../utils.js';
    import { userId, appLang, csrfToken, regionsType, appName } from '../../constants';
    import { exactSvg, partialSvg, semanticSvg, noSvg, userSvg, validateSvg } from './similarityCategory';

    import Region from "../Region.svelte";

    ////////////////////////////////////////////

    const windowUrl = new URL(window.location.href)
    const baseUrl = windowUrl.origin;
    const pathUrl = windowUrl.pathname;

    /** @type {string} */
    export let qImg;
    /** @type {string} */
    export let sImg;
    /** @type {number} */
    export let qRegions;
    /** @type {number} */
    export let sRegions;
    /** @type {number} */
    export let score = 0;
    /** @type {number?} */
    export let category = null;
    /** @type {number?[]} */
    export let users = [];
    /** @type {boolean} */
    export let isManual;
    /** @type {number} */
    export let similarityType;

    const { getRegionsInfo, comparedRegions } = similarityStore;

    const isPropagatedContext = getContext("similarityPropagatedContext") || false;  // true if it's a propagation, false otherwise

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

    $: selectedCategory = category;
    $: isSelectedByUser = users.includes(Number(userId)) || false;

    ////////////////////////////////////////////

    /**
     * if the current SimilarRegion is a propagation, then
     * `similarityStore.comparedRegions` may not contain the `regions`.
     * in that case, we fetch the title from the backend.
     * @returns {Promise<string>}
     *      if `!isPropagatedContext` the result could be synchronous, but
     *      it is returned as a promise to provide the same async interface
     *      for both branches
     */
    async function getDesc() {
        const formatter = (title) =>
            `${title}<br>
            Page ${parseInt(canvas)}<br>
            <b>${
                !isNaN(parseFloat(score)) && similarityType === 1
                ? `Score: ${score}`
                : similarityType === 2 && appLang === 'en'
                ? 'Manual similarity'
                : similarityType === 2 && appLang === 'fr'
                ? 'Correspondance manuelle'
                : similarityType === 3 && appLang === 'en'
                ? 'Propagated match'
                : 'Correspondance propagée'
            }</b>`;
        return isPropagatedContext===true
            ? fetch(`${baseUrl}${pathUrl}get_regions_title/${regionRef}`)
                .then(r => r.json())
                .then(r => formatter(r.title))
                .catch(e => {
                    console.error("SimilarRegion.getDesc()", e);
                    return formatter(appLang === "fr" ? "Titre inconnu" : "Unknown title");
                })
            : Promise.resolve(formatter(getRegionsInfo(regionRef).title));
    }

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

    // format the current SimilarRegion to send to the backend
    const toRegionPair = () => ({
        img_1: qImg,
        img_2: sImg,
        regions_id_1: qRegions,
        regions_id_2: sRegions,
        score: score,
        category: selectedCategory,
        category_x: updateCurrentUsers(users),
        is_manual: isManual || similarityType === 2,
        similarity_type: similarityType
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
     * if `similarityType===3` (propagated match), the RegionPair does not exist in the DB.
     * setting the region will create the RegionPair and and save it to database
     */
    async function categorize(category) {
        updateCategory(category);
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
            }
        } catch (error) {
            console.error('Error:', error);
            // unselect category
            updateCategory(category);
        }
    }
</script>


<div>
    <!-- TODO remove selection outline from SimilarRegion in similarities
        (selecting a Region has no effect on "Selection") -->
    <Region {item} size={256} descPromise={getDesc()} isSquare={false}/>
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

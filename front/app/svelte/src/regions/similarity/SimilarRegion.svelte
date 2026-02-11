<script>
    import { getContext, setContext } from "svelte";

    import { userId, csrfToken, appName } from '../../constants';
    import { toRegionItem } from "../utils.js";

    import CategoryButton from "./CategoryButton.svelte";
    import {extractInt, shorten} from "../../utils.js";
    import {similarityStore} from "./similarityStore.js";
    import RegionCard from "../RegionCard.svelte";

    const {comparedRegions} = similarityStore;

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */
    /** @typedef {import("./types.js").SimilarityPairType} SimilarityPairType */

    ////////////////////////////////////////////

    const windowUrl = new URL(window.location.href)
    const baseUrl = windowUrl.origin;

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
    /** @type {number|null} */
    export let category = null;
    /** @type {number|null[]} */
    export let users = [];
    /** @type {boolean} */
    export let isManual;
    /** @type {number} */
    export let similarityType;
    /** @type {number} */
    export let index = 0;
    /** @type {boolean} */
    export let isInModal = false;

    const [wit, digit, canvas, xywh] = sImg.split('.')[0].split('_');

    const toTitledRegion = () => {
        let item = toRegionItem(sImg, wit, xywh, canvas);
        const regionData = $comparedRegions[`${wit}_${digit}_anno${sRegions}`] || {title: item.title};
        item.title = `${shorten(regionData.title.replace(/^[^|]+/, ""))}<br/>Page ${extractInt(canvas)}<br/><b>Score: ${score}</b>`;
        return item;
    }

    /** @type {RegionItemType} */
    const item = toTitledRegion();

    $: selectedCategory = category;
    $: isSelectedByUser = users.includes(Number(userId)) || false;

    /** @type {SimilarityPairType} we set the whole similarity pair as a context object so that it can be used by the descendant ModalSimilarity and its descendants if needed */
    setContext("similarityPair", {
        qImg: qImg,
        sImg: sImg,
        qRegions: qRegions,
        sRegions: sRegions,
        score: score,
        category: category,
        users: users,
        isManual: isManual,
        similarityType: similarityType,
    });

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

    // format the current SimilarRegion to send to the backend
    const toRegionPair = () => ({
        img_1: qImg,
        img_2: sImg,
        regions_id_1: qRegions,
        regions_id_2: sRegions,
        score: score,
        category: selectedCategory,
        category_x: updateCurrentUsers(users),
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
     * setting the region will create the RegionPair and save it to database
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
    <RegionCard {item} height={140} selectable={false} copyable={true} isSquare={false} {isInModal} {index} on:openModal/>
    {#if !isInModal}
        <div class="tags has-addons is-dark is-center">
            <CategoryButton category={1} isSelected={selectedCategory === 1} toggle={categorize} padding="pl-3 pr-2"/>
            <CategoryButton category={2} isSelected={selectedCategory === 2} toggle={categorize}/>
            <CategoryButton category={3} isSelected={selectedCategory === 3} toggle={categorize}/>
            <CategoryButton category={4} isSelected={selectedCategory === 4} toggle={categorize}/>
            <CategoryButton category={5} isSelected={selectedCategory === 5} toggle={categorize} padding="pl-2 pr-3"/>
        </div>
    {/if}
</div>

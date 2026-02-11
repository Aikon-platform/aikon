<script>
    import { setContext } from "svelte";

    import { userId, csrfToken, appName } from "../../constants";
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
    /** @type {number} */
    export let similarityType;
    /** @type {string}*/
    export let similarityHash;
    /** @type {number} */
    export let index = 0;
    /** @type {boolean} */
    export let isInModal = false;

    const [wit, digit, canvas, xywh] = sImg.split(".")[0].split("_");

    /** @type {RegionItemType} */
    const item = toTitledRegion();

    let selectedCategory = category;

    ////////////////////////////////////////////

    function toTitledRegion() {
      let item = toRegionItem(sImg, wit, xywh, canvas);
      const regionData = $comparedRegions[`${wit}_${digit}_anno${sRegions}`] || {title: item.title};
      item.title = `${shorten(regionData.title.replace(/^[^|]+/, ""))}<br/>Page ${extractInt(canvas)}<br/><b>Score: ${score}</b>`;
      return item;
    }

    // format the current SimilarRegion to send to the backend
    const toRegionPair = (currentUsers) => ({
      img_1: qImg,
      img_2: sImg,
      regions_id_1: qRegions,
      regions_id_2: sRegions,
      score: score,
      category: selectedCategory,
      category_x: currentUsers,
      similarity_type: similarityType,
      similarity_hash: similarityHash
    })

    const usersIncludesCurrentUser = (currentUsers) =>
      currentUsers.includes(Number(userId));

    const updateCategory = (newCategory, oldCategory) =>
      newCategory === oldCategory ? null : newCategory;

    const updateUsers = (newCategory, currentUsers) => {
      console.log("updateUsers", newCategory, currentUsers);
      currentUsers = currentUsers.slice()
      if ( !usersIncludesCurrentUser(currentUsers) ) {
        return [ ...currentUsers, Number(userId) ];
      } else {
        return currentUsers// .filter((_userId) => Number(userId) !== _userId );
      }
    }

    /**
     * save the new RegionPair.category to database (RegionPair.category)
     * if `similarityType===3` (propagated match), the RegionPair does not exist in the DB.
     * setting the region will create the RegionPair and save it to database
     */
    async function categorize(category) {
      selectedCategory = updateCategory(category, selectedCategory);
      let currentUsers = updateUsers(selectedCategory, users);
      console.log("OLD CURRENT USERS", users);
      console.log("NEW SELECTED CATEGORY", selectedCategory);
      console.log("NEW CURRENT USERS", currentUsers);

      try {
        const response = await fetch(`${baseUrl}/${appName}/save-category`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          },
          body: JSON.stringify(toRegionPair(currentUsers))
        });
        if (!response.ok) {
          console.error("Error: Network response was not ok");
          // unselect category
          selectedCategory = updateCategory(category);
        }
      } catch (error) {
        console.error("Error:", error);
        // unselect category
        selectedCategory = updateCategory(category);
      }
    }
</script>

<div>
    <RegionCard {item} height={140} selectable={false} copyable={true} isSquare={false} {isInModal} {index} on:openModal/>
    {#if !isInModal}
        <h2>{selectedCategory}</h2>
        <div class="tags has-addons is-dark is-center">
            <CategoryButton category={1} isSelected={selectedCategory === 1} toggle={categorize} padding="pl-3 pr-2"/>
            <CategoryButton category={2} isSelected={selectedCategory === 2} toggle={categorize}/>
            <CategoryButton category={3} isSelected={selectedCategory === 3} toggle={categorize}/>
            <CategoryButton category={4} isSelected={selectedCategory === 4} toggle={categorize}/>
            <CategoryButton category={5} isSelected={selectedCategory === 5} toggle={categorize} padding="pl-2 pr-3"/>
        </div>
    {/if}
</div>

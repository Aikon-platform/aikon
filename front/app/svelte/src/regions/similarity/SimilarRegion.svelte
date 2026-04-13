<script>
    import { userId, csrfToken, appName, appLang } from "../../constants";
    import { RegionItem } from "../types.js";

    import CategoryButton from "./CategoryButton.svelte";
    import {i18n, shorten, showMessage} from "../../utils.js";
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
    // /** @type {number} */
    // export let qRegions; // TO DELETE
    /** @type {number} */
    export let sRegions; // TO DELETE
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

    let selectedCategory = category;
    let isSelectedByUser = usersIncludesCurrentUser(users);

    ////////////////////////////////////////////

    const t = {
        deletePair: {
            en: "Delete pair",
            fr: "Supprimer la paire"
        },
        confirmDelete: {
            en: "Do you confirm this pair should be deleted?",
            fr: "Confirmez-vous que cette paire doit être supprimée ?"
        },
    };

    const sImgItem = RegionItem.fromImg(sImg);
    function toTitledRegion() {
        const regionData = $comparedRegions[`wit${sImgItem.witnessId}_${sImgItem.digitType}${sImgItem.digitId}_anno${sRegions}`] || {title: sImgItem.title};
        sImgItem.title = `${shorten(regionData.title.replace(/^[^|]+/, ""))}<br/>Page ${sImgItem.canvasNb}`;
        if (score) {
            sImgItem.title += `<br/><b>Score: ${score}</b>`;
        }
        return sImgItem;
    }
    const item = toTitledRegion();

    // // format the current SimilarRegion to send to the backend
    // const toRegionPair = (currentUsers) => ({
    //     img_1: qImg,
    //     img_2: sImg,
    //     regions_id_1: qRegions,
    //     regions_id_2: sRegions,
    //     score: score,
    //     category: selectedCategory,
    //     category_x: currentUsers,
    //     similarity_type: similarityType,
    //     similarity_hash: similarityHash
    // })

    function usersIncludesCurrentUser (currentUsers) {
        return currentUsers.includes(Number(userId));
    }

    /**
     * save the new RegionPair.category to database (RegionPair.category)
     * if `similarityType===3` (propagated match), the RegionPair does not exist in the DB.
     * setting the region will create the RegionPair and save it to database
     */
    async function categorize(category) {
        const previousCategory = selectedCategory;
        selectedCategory = selectedCategory === category ? null : category;

        try {
            const response = await fetch(`${baseUrl}/${appName}/save-category`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    img_1: qImg,
                    img_2: sImg,
                    category: selectedCategory,
                    similarity_type: similarityType,
                    similarity_hash: similarityHash
                })
            });
            if (!response.ok) {
                console.error("Error: Network response was not ok");
                selectedCategory = previousCategory;
            }
        } catch (error) {
            console.error("Error:", error);
            selectedCategory = previousCategory;
        }
    }

    async function addUserToPair() {
        const previousState = isSelectedByUser;
        isSelectedByUser = !isSelectedByUser;

        try {
            const response = await fetch(`${baseUrl}/${appName}/add-user-to-pair`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ img_1: qImg, img_2: sImg })
            });
            if (!response.ok) {
                console.error("Error: Network response was not ok");
                isSelectedByUser = previousState;
            }
        } catch (error) {
            console.error("Error:", error);
            isSelectedByUser = previousState;
        }
    }

    async function deletePair() {
        const confirmed = await showMessage(
            i18n("confirmDelete", t), i18n("confirm"), true
        );
        if (!confirmed) return;
        try {
            const response = await fetch(`${baseUrl}/${appName}/delete-pair`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ q_img: qImg, s_img: sImg })
            });
            if (!response.ok) {
                console.error("Error: Network response was not ok");
                return;
            }
            similarityStore.triggerRefresh();
        } catch (error) {
            console.error("Error:", error);
        }
    }
</script>

<div class="cell">
    <RegionCard {item} height={140} selectable={false} copyable={true} isSquare={false} {isInModal} {index} on:openModal>
        <svelte:fragment slot="actions">
            {#if isInModal}
                <button class="button tag" on:click|stopPropagation={deletePair}
                        title="{i18n('deletePair', t)}">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path stroke="#ff6685" fill="none" stroke-width="2" d="M18 6L17.1991 18.0129C17.129 19.065 17.0939 19.5911 16.8667 19.99C16.6666 20.3412 16.3648 20.6235 16.0011 20.7998C15.588 21 15.0607 21 14.0062 21H9.99377C8.93927 21 8.41202 21 7.99889 20.7998C7.63517 20.6235 7.33339 20.3412 7.13332 19.99C6.90607 19.5911 6.871 19.065 6.80086 18.0129L6 6M4 6H20M16 6L15.7294 5.18807C15.4671 4.40125 15.3359 4.00784 15.0927 3.71698C14.8779 3.46013 14.6021 3.26132 14.2905 3.13878C13.9376 3 13.523 3 12.6936 3H11.3064C10.477 3 10.0624 3 9.70951 3.13878C9.39792 3.26132 9.12208 3.46013 8.90729 3.71698C8.66405 4.00784 8.53292 4.40125 8.27064 5.18807L8 6"/>
                    </svg>
                </button>
            {/if}
        </svelte:fragment>
    </RegionCard>
    <div class="tags has-addons is-dark is-center">
        <CategoryButton category={1} isSelected={selectedCategory === 1} toggle={categorize} padding="pl-3 pr-2"/>
        <CategoryButton category={2} isSelected={selectedCategory === 2} toggle={categorize}/>
        <CategoryButton category={3} isSelected={selectedCategory === 3} toggle={categorize}/>
        <CategoryButton category={4} isSelected={selectedCategory === 4} toggle={categorize}/>
        <CategoryButton category={5} isSelected={isSelectedByUser} toggle={addUserToPair} padding="pl-2 pr-3"/>
    </div>
</div>

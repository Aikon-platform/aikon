<script>
    import { userId, csrfToken, appName } from "../../constants";
    import CategoryToolbar from "./CategoryToolbar.svelte";

    export let qImg;
    export let sImg;
    export let category = null;
    export let users = [];
    export let isSelectedByUser = users.includes(Number(userId));
    export let similarityType = null;
    export let similarityHash = null;

    const post = (endpoint, body) => fetch(`${window.location.origin}/${appName}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify(body)
    }).then(r => r.ok).catch(e => (console.error("Error:", e), false));

    /**
     * if `similarityType===3` (propagated match), the RegionPair does not exist in the DB.
     * setting the category will create the RegionPair and save it to database
     */
    async function categorize(cat) {
        const previous = category;
        category = category === cat ? null : cat;
        const ok = await post("save-category", {
            img_1: qImg, img_2: sImg, category, similarity_type: similarityType, similarity_hash: similarityHash
        });
        if (!ok) category = previous;
    }

    async function addUserToPair() {
        isSelectedByUser = !isSelectedByUser;
        if (!await post("add-user-to-pair", { img_1: qImg, img_2: sImg })) isSelectedByUser = !isSelectedByUser;
    }
</script>

<CategoryToolbar selectedCategory={category} {isSelectedByUser} toggleFct={categorize} userToggleFct={addUserToPair}/>

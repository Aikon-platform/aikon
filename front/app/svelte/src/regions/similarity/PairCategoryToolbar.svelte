<script>
    import { userId, csrfToken, appName } from "../../constants";
    import CategoryToolbar from "./CategoryToolbar.svelte";

    /**
     * @typedef {Object} Props
     * @property {any} qImg
     * @property {any} sImg
     * @property {any} [category]
     * @property {any} [users]
     * @property {any} [isSelectedByUser]
     * @property {any} [similarityType]
     * @property {any} [similarityHash]
     * @property {any} [onChange]
     */

    /** @type {Props} */
    let {
        qImg,
        sImg,
        category = $bindable(null),
        users = [],
        isSelectedByUser = $bindable(users.includes(Number(userId))),
        similarityType = null,
        similarityHash = null,
        onChange = () => {}
    } = $props();

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
        ok ? onChange(category) : category = previous;
    }

    async function addUserToPair() {
        isSelectedByUser = !isSelectedByUser;
        if (!await post("add-user-to-pair", { img_1: qImg, img_2: sImg, similarity_type: similarityType })) {
            isSelectedByUser = !isSelectedByUser;
        }
    }
</script>

<CategoryToolbar selectedCategory={category} {isSelectedByUser} toggleFct={categorize} userToggleFct={addUserToPair}/>

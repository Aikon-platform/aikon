<script>
    import { categoryInfo } from "./similarityCategory.js";
    import {i18n} from "../../utils.js";

    export let selectable = true;
    export let isSelected = false;
    export let category;
    export let toggle = () => {};
    export let padding = "px-2";

    const categoryTitle = categoryInfo[category].title;

    const t = {
        categorize: {en: `Categorize as “${categoryTitle}”`, fr: `Catégoriser comme « ${categoryTitle} »`},
        uncategorize: {en: `Remove “${categoryTitle}” category`, fr: `Retirer la catégorie « ${categoryTitle} »`},
    }

    const catTitle = () => {
        if (!selectable) return categoryTitle
        return isSelected ? i18n("uncategorize", t) : i18n("categorize", t);
    }
</script>

<span class="tag py-4 {padding} {selectable ? 'is-hoverable' : ''}" class:is-selected={isSelected}
      on:click={() => toggle(category)} on:keyup={null} title={catTitle()}>
    {@html categoryInfo[category].svg}
</span>

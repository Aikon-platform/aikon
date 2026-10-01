<script>
    import { createEventDispatcher } from "svelte";
    import { appName } from "../../constants.js";
    import { i18n, sendTo, showMessage } from "../../utils.js";
    import { RegionItem } from "../types.js";
    import RegionCard from "../RegionCard.svelte";
    import CategoryToolbar from "../similarity/CategoryToolbar.svelte";

    export let q;
    export let s;
    export let keep;
    export let indexed;
    export let iou = null;
    export let deletion = null;
    export let conflicts = [];

    const dispatch = createEventDispatcher();
    const t = {
        chooseKept: { en: "Select the region to keep", fr: "Sélectionnez la région à conserver" },
        otherPage: { en: "different pages", fr: "pages différentes" },
        indexed: { en: "Indexed region", fr: "Région indexée" },
        notIndexed: { en: "Nonexistent region", fr: "Région inexistante" },
        resolveConflicts: {
            en: "These pairs have conflicting categories: choose the one to keep",
            fr: "Ces paires ont des catégories contradictoires : choisissez celle à conserver"
        },
        confirmDelete: {
            en: "The two boxes overlap by less than 90%. Also delete the annotation of the discarded region?",
            fr: "Les deux boîtes se recouvrent à moins de 90 %. Supprimer aussi l'annotation de la région écartée ?"
        },
        next: { en: "Next", fr: "Suivant" },
        merge: { en: "Merge", fr: "Fusionner" },
        cancel: { en: "Cancel", fr: "Annuler" },
        networkPb: { en: "Problem with network", fr: "Problème de réseau" },
    };

    let step = "bbox";
    let categories = Object.fromEntries(conflicts.map(c => [c.img, Math.min(...c.categories)]));
    $: drop = keep === q ? s : q;
    $: next = step === "bbox" && conflicts.length > 0;

    const toggle = (img) => (cat) => categories[img] = categories[img] === cat ? null : cat;

    async function merge() {
        if (next) return step = "conflicts";
        const deleteDrop = deletion === "ask" && await showMessage(i18n("confirmDelete", t), i18n("confirm"), true);
        const data = await sendTo(`${appName}/similarity/merge-regions`,
            { keep, drop, categories, delete_drop: deleteDrop }, i18n("networkPb", t));
        if (data) dispatch("merged", data);
    }
</script>

<div class="is-overlay is-flex is-flex-direction-column is-align-items-center is-justify-content-center p-5 box"
     style="background-color: var(--bulma-body-background-color); z-index: 10; overflow: auto">
    {#if step === "bbox"}
        <p class="mb-4">{i18n("chooseKept", t)} ({iou === null ? i18n("otherPage", t) : `IoU ${iou.toFixed(2)}`})</p>
        <div class="is-flex is-gap-4">
            {#each [q, s] as img (img)}
                <div class="is-clickable has-text-centered" style:opacity={img === keep ? 1 : 0.5}
                     on:click={() => keep = img} on:keyup={null}>
                    <RegionCard item={RegionItem.fromImg(img)} height={250} isInModal={true} selectable={false} downloadable={false}
                                borderColor={img === keep ? "var(--bulma-link)" : null}/>
                    <span class="tag is-light" class:is-link={indexed[img]}>{i18n(indexed[img] ? "indexed" : "notIndexed", t)}</span>
                </div>
            {/each}
        </div>
    {:else}
        <p class="mb-4">{i18n("resolveConflicts", t)}</p>
        <div class="grid is-gap-3 has-4-cols">
            {#each conflicts as { img } (img)}
                <div class="cell">
                    <RegionCard item={RegionItem.fromImg(img)} height={140} isInModal={true} selectable={false} downloadable={false}/>
                    <CategoryToolbar visibleCategories={[1, 2, 3, 4]} selectedCategory={categories[img]} toggleFct={toggle(img)}/>
                </div>
            {/each}
        </div>
    {/if}
    <div class="buttons mt-4">
        <button class="button is-link" on:click={merge}>{i18n(next ? "next" : "merge", t)}</button>
        <button class="button" on:click={() => dispatch("cancel")}>{i18n("cancel", t)}</button>
    </div>
</div>

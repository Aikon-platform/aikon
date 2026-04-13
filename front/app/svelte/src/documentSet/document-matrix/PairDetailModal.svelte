<script>
    import {onMount, onDestroy, createEventDispatcher} from "svelte";
    import {closeModal, refToIIIF, i18n, showMessage} from "../../utils.js";
    import {appName, appUrl, csrfToken} from "../../constants.js";
    import NavigationArrow from "../../ui/NavigationArrow.svelte";
    import {RegionItem} from "../../regions/types.js";
    import { categoryInfo } from "../../regions/similarity/similarityCategory.js";

    export let active = false;
    export let scatterData = null;
    export let navState = null; // {idx1, idx2}
    export let pairs = [];

    const dispatch = createEventDispatcher();

    const t = {
        score: {en: "Score", fr: "Score"},
        exact: {en: "Exact match", fr: "Correspondance exacte"},
        failed: {en: "Categorization failed", fr: "La catégorisation a échoué"},
        categorize: {en: "Categorize as exact match", fr: "Catégoriser comme correspondance exacte"},
        uncategorize: {en: "Remove exact match category", fr: "Retirer la catégorie « correspondance exacte »"},
    };

    function findPair(img1, img2) {
        return pairs.find(p =>
            (p.id_1 === img1 && p.id_2 === img2) ||
            (p.id_1 === img2 && p.id_2 === img1)
        );
    }

    let updateTick = 0;
    async function categorize(isExact) {
        if (!modalData?.canCategorize) return;
        try {
            const response = await fetch(`${appUrl}/${appName}/save-category`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    img_1: modalData.img1,
                    img_2: modalData.img2,
                    category: isExact ? null : 1,
                })
            });
            if (response.ok) {
                const match = findPair(modalData.img1, modalData.img2);
                const newCat = isExact ? null : 1;
                if (match) match.category = newCat;
                updateTick++;
                // dispatch("categorize");
                return true;
            }
            await showMessage( i18n("failed, t"), i18n("error"));
            return false;
        } catch (error) {
            await showMessage(
                error,
                i18n("error"),
            );
            console.error("Error:", error);
        }
    }

    let modalElement;

    $: navLimits = scatterData ? getNavLimits(scatterData) : {max1: 0, max2: 0};
    $: modalData = navState && scatterData && navLimits ? buildModalData(navState, scatterData, navLimits, updateTick) : null;


    function getNavLimits(data) {
        if (data.mode === "image") return {max1: data.images1.length, max2: data.images2.length};
        const maxPage1 = Math.max(...data.points.map(p => p.page1));
        const maxPage2 = Math.max(...data.points.map(p => p.page2));
        return {max1: maxPage1, max2: maxPage2};
    }

    function getPageImageUrl(doc, pageNum) {
        return new RegionItem(doc.images[0]).urlForCanvas(pageNum, "full", "600,");
    }

    function getRegionImageUrl(img) {
        // TODO use RegionItem.urlForRegion()
        return refToIIIF(img.ref, img.xywh?.join(","), "600,");
    }

    function buildModalData(nav, data, limits, _tick) {
        if (!nav || !data || !limits) return null;
        const {doc1, doc2} = data;

        let result;

        if (data.mode === "image") {
            const img1 = data.images1?.[nav.idx1], img2 = data.images2?.[nav.idx2];
            if (!img1 || !img2) return null;

            const pair = data.pairScores.get(`${nav.idx1}-${nav.idx2}`);
            result = {
                items: [
                    {doc: doc1, label: `Canvas ${img1.canvas} — Image #${nav.idx1 + 1}`, imgUrl: getRegionImageUrl(img1)},
                    {doc: doc2, label: `Canvas ${img2.canvas} — Image #${nav.idx2 + 1}`, imgUrl: getRegionImageUrl(img2)}
                ],
                score: pair?.score,
                canCategorize: true,
                img1: img1.id,
                img2: img2.id,
            };
        } else {
            const page1 = nav.idx1 + 1, page2 = nav.idx2 + 1;
            const point = data.points.find(p => p.page1 === page1 && p.page2 === page2);

            const imgsOnPage1 = doc1.images?.filter(img => img.canvas === page1) || [];
            const imgsOnPage2 = doc2.images?.filter(img => img.canvas === page2) || [];
            const singlePair = imgsOnPage1.length === 1 && imgsOnPage2.length === 1;

            result = {
                items: [
                    {doc: doc1, label: `Page ${page1}`, imgUrl: getPageImageUrl(doc1, page1)},
                    {doc: doc2, label: `Page ${page2}`, imgUrl: getPageImageUrl(doc2, page2)},
                ],
                score: point?.score,
                canCategorize: singlePair,
                img1: singlePair ? imgsOnPage1[0].id : null,
                img2: singlePair ? imgsOnPage2[0].id : null,
            };
        }

        const match = result.img1 && result.img2 ? findPair(result.img1, result.img2) : null;
        result.isExact = match?.category === 1;
        return result;
    }

    function navigate(delta, axis) {
        if (!navState || !scatterData) return;
        if (axis === "horizontal") {
            navState.idx1 = (navState.idx1 + delta + navLimits.max1) % navLimits.max1;
        } else {
            navState.idx2 = (navState.idx2 + delta + navLimits.max2) % navLimits.max2;
        }
        dispatch("navigate", navState);
    }

    function handleKeydown(e) {
        if (!active || !navState) return;
        const keyMap = {
            ArrowUp: [-1, "vertical"],
            ArrowDown: [1, "vertical"],
            ArrowLeft: [-1, "horizontal"],
            ArrowRight: [1, "horizontal"]
        };
        const action = keyMap[e.key];
        if (action) { e.preventDefault(); navigate(action[0], action[1]); }
    }

    function handleClose() {
        dispatch("close");
    }

    onMount(() => window.addEventListener("keydown", handleKeydown));
    onDestroy(() => window.removeEventListener("keydown", handleKeydown));

    $: if (modalElement) active ? modalElement.classList.add("is-active") : modalElement.classList.remove("is-active");
</script>

<div class="modal" bind:this={modalElement} use:closeModal on:close={handleClose}>
    <div class="modal-background" on:click={handleClose} on:keyup={null}></div>
    <div class="modal-content" style="width: auto; max-width: 70vw;">
        <div class="box p-5">
            {#if modalData}
                <table class="table is-fullwidth p-3 has-text-centered">
                    <thead>
                        <tr>
                            {#each modalData.items as item}
                                <th class="doc-title">
                                    <span style="color:{item.doc.color}">●</span>
                                    <strong>{item.doc.title}</strong>
                                    <p class="is-size-7 has-text-grey mt-2">{item.label}</p>
                                </th>
                            {/each}
                        </tr>
                    </thead>
                    <tbody>
                        {#if modalData.score !== undefined || modalData.canCategorize}
                            <tr>
                                <td colspan="2" class="has-text-centered">
                                    <div class="field has-addons has-addons-centered">
                                        {#if modalData.score !== undefined}
                                            <p class="control">
                                                <span class="button is-small is-light is-static">
                                                    {i18n("score", t)} {modalData.score.toFixed(2)}
                                                </span>
                                            </p>
                                        {/if}
                                        {#if modalData.canCategorize}
                                            {@const isExact = modalData.isExact}
                                            <p class="control" title={i18n(isExact ? "uncategorize" : "categorize", t)}}>
                                                <button class="button is-small is-link" class:is-inverted={!isExact} on:click={() => categorize(isExact)}>
                                                    {@html categoryInfo[1].svg}
                                                    <span class="pl-2">{i18n("exact", t)}</span>
                                                </button>
                                            </p>
                                        {/if}
                                    </div>
                                </td>
                            </tr>
                        {/if}
                        <tr>
                            {#each modalData.items as item, i}
                                <td class="modal-cell">
                                    <div class="image-nav-container">
                                        <NavigationArrow direction={i !== 0 ? "up" : "left"} delta={-1} axis={i !== 0 ? "vertical" : "horizontal"} navigationFct={navigate}/>
                                        <figure class="image">
                                            <img src={item.imgUrl} alt="{scatterData?.mode === 'image' ? 'Image' : 'Page'} {item.label}" class="img-preview"/>
                                        </figure>
                                        <NavigationArrow direction={i !== 0 ? "down" : "right"} delta={1} axis={i !== 0 ? "vertical" : "horizontal"} navigationFct={navigate}/>
                                    </div>
                                </td>
                            {/each}
                        </tr>
                    </tbody>
                </table>
            {/if}
        </div>
    </div>
    <button class="modal-close is-large" aria-label="close" on:click={handleClose}></button>
</div>

<style>
    .doc-title {
        width: 50%;
        text-align: center !important;
        vertical-align: middle;
    }
    .modal-cell {
        width: 50%;
        vertical-align: middle;
    }
    .image-nav-container {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 1em 0;
    }
    .img-preview {
        border-radius: 5px;
        max-height: 600px;
        max-width: 90%;
        margin: 2em auto;
    }
</style>

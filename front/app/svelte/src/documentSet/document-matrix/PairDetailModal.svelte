<script>
    import {onMount, onDestroy, createEventDispatcher} from "svelte";
    import {closeModal, refToIIIF, i18n, sendTo} from "../../utils.js";
    import {appName} from "../../constants.js";
    import NavigationArrow from "../../ui/NavigationArrow.svelte";
    import {RegionItem} from "../../regions/types.js";
    import CategoryToolbar from "../../regions/similarity/CategoryToolbar.svelte";

    export let active = false;
    export let scatterData = null;
    export let navState = null; // {idx1, idx2}
    export let pairCat = new Map();

    const dispatch = createEventDispatcher();

    const t = {
        score: {en: "Score", fr: "Score"},
        failed: {en: "Categorization failed", fr: "La catégorisation a échoué"},
    };

    function findCat(img1, img2) {
        return pairCat.get(`${img1}-${img2}`) ?? pairCat.get(`${img2}-${img1}`) ?? null;
    }

    let updateTick = 0;
    async function categorize(category) {
        if (!modalData?.canCategorize) return;
        const newCat = modalData.category === category ? null : category;
        const ok = await sendTo(`${appName}/save-category`, {
            img_1: modalData.img1,
            img_2: modalData.img2,
            category: newCat,
        }, i18n("failed", t));

        if (!ok) return;

        pairCat.set(`${modalData.img1}-${modalData.img2}`, newCat);
        updateTick++;
    }

    let modalElement;

    $: navLimits = scatterData ? getNavLimits(scatterData) : {max1: 0, max2: 0};
    $: modalData = navState && scatterData && navLimits ? buildModalData(navState, scatterData, navLimits, updateTick, pairCat) : null;

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

    function buildModalData(nav, data, limits, _tick, _pairCat) {
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

        result.category = result.img1 && result.img2 ? findCat(result.img1, result.img2) : null;

        console.log(result);
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
                                    {#if modalData.score !== undefined}
                                        <span class="tag button is-small is-contrasted pb-3">
                                            {i18n("score", t)} {modalData.score.toFixed(2)}
                                        </span>
                                    {/if}

                                    {#if modalData.canCategorize}
                                        <CategoryToolbar visibleCategories={[1,2,3,4]}
                                            selectedCategory={modalData.category}
                                            toggleFct={categorize}/>
                                    {/if}
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

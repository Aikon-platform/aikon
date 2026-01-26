<!--
    general functioning:
    - different components are displayed depending on the context in which this component is used:
        - for "normal" regions, only ModalRegion will be used
        - for similarities, `ModalRegion`, `ModalSimilarity`, `ModalQueryExpansion` will be used
    - `allowedViewIds` defines which views (aka, components) can be used in this modal,
      based on the props passed to it. each view is identified by a unique string.
    - `currentViewId` is a value of `allowedViewIds`
    - other data variables are derived from `allowedViewIds`: they are objects or arrays which map
      a reference to a value of `allowedViewIds` to extra data for a specific view (i.e. a component reference).
    - tabs allow to switch between components. internally, `toggleView` will set a new `currentViewId`,
      which, by side-effects, will render a new component
-->

<script>
    import { onMount, onDestroy, createEventDispatcher } from "svelte";

    import { appLang } from "../../constants.js";

    import ModalRegion from "./ModalRegion.svelte";
    import ModalPage from "./ModalPage.svelte";
    import ModalVectorization from "./ModalVectorization.svelte";
    import { RegionItem } from "../types.js";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */
    /** @typedef {"main"|"page"|"similarity"|"expansion"} ViewIdType */

    //////////////////////////////////////////////////

    /** @type {RegionItemType} */
    export let mainImgItem;
    /** @type {RegionItemType} */
    export let compareImgItem;
    export let svgItem;
    /** @type {RegionItemType[]} */
    export let items = null;
    /** @type {number} */
    export let initialIndex = null;

    $: canNavigate = items?.length > 1;
    $: currentIndex = initialIndex ?? 0;
    $: if (canNavigate && items[currentIndex]) {
        mainImgItem = new RegionItem(items[currentIndex]);
    }

    const navigate = (delta) => {
        if (!canNavigate) return;
        currentIndex = (currentIndex + delta + items.length) % items.length;
    };

    const dispatch = createEventDispatcher();

    /** @type {ViewIdType[]} */
    const allowedViewIds =
        compareImgItem
        ? [ "main", "page", "similarity", "expansion" ]
        : svgItem
            ? [ "overlay" ]
            : [ "main", "page" ];


    const labels = {
        expansion: { fr: "Expansion de requête", en: "Query expansion" },
        similarity: { fr: "Comparaison", en: "Comparison" },
        page: { fr: "Vue de la page", en: "Page view" },
        main: { fr: "Vue principale", en: "Main view" },
        overlay: { fr: "Vue superposée", en: "Overlay view"}
    };

    /** @type { {id:ViewIdType, label:string}[] } */
    const viewTabs = allowedViewIds.map((viewId) => ({
        id: viewId,
        label: labels[viewId]?.[appLang] ?? "Main view"
    }));

    /**
     * @type {{ [ViewIdType]: SvelteComponent }} viewId mapped to the relevant component instance.
     * by default, only ModalRegion is defined. other components qre imported asynchronously,
     * after which viewComponents is updated
     */
    const viewComponents = {
        main: ModalRegion,
        page: ModalPage,
        overlay: ModalVectorization,
    };
    if ( compareImgItem ) {
        Promise.all([
            import("./ModalSimilarity.svelte").then(res => res.default),
            import("./ModalQueryExpansion.svelte").then(res => res.default),
        ]).then(([modalSimilarityComponent, modalQueryExpansionComponent]) => {
            // we loop over `allowedViewIds`, but check that those haven't been already
            // mapped to a component in `viewComponents`. else, we risk overwriting the component
            const predefinedViews = Object.keys(viewComponents);
            allowedViewIds
                .filter(viewId => !predefinedViews.includes(viewId))
                .map((viewId) =>
                    viewComponents[viewId] =
                        viewId==="expansion"
                        ? modalQueryExpansionComponent
                        : viewId==="similarity"
                        ? modalSimilarityComponent
                        : ModalRegion
                );
        })
    }

        $: viewProps = {
            main: { mainImgItem },
            page: { mainImgItem },
            similarity: { mainImgItem, compareImgItem },
            overlay: { svgItem },
            expansion: { mainImgItem, compareImgItem },
        };
        // allowedViewIds.forEach(viewId => {
        //     if (viewId === "similarity") {
        //         viewProps[viewId] = { mainImgItem, compareImgItem };
        //     } else if (viewId === "overlay") {
        //         viewProps[viewId] = { svgItem };
        //     } else {
        //         viewProps[viewId] = { mainImgItem };
        //     }
        // });

    /** @type {ViewIdType} */
    $: currentViewId = allowedViewIds[0];

    //////////////////////////////////////////////////

    const toggleView = (viewId) => currentViewId = viewId;

    const onKeyUp = (e) => {
        if (e.key === "Escape") dispatch("closeModal");
        else if (e.key === "ArrowLeft") navigate(-1);
        else if (e.key === "ArrowRight") navigate(1);
    };

    const onClose = () => dispatch("closeModal");

    //////////////////////////////////////////////////

    onMount(() => {
        document.addEventListener("keyup", onKeyUp);
    })
    onDestroy(() => {
        document.removeEventListener("keydown", onKeyUp);
    })
</script>


<div id="region-modal-wrapper" class="modal is-active">
    <div class="modal-background" on:click={onClose} on:keyup={onKeyUp}/>
    <div class="modal-content">
        {#if canNavigate}
            <button class="nav-btn nav-left" on:click={() => navigate(-1)}>
                <span class="icon"><i class="fas fa-chevron-left"/></span>
            </button>
        {/if}

        <div class="modal-inner">
            <div class="tabs is-centered" style="height: fit-content;">
                <ul>
                    {#each viewTabs as { id, label }}
                        <li class={id===currentViewId ? "is-active": ""}>
                            <!-- svelte-ignore a11y-invalid-attribute -->
                            <a on:click|preventDefault={() => toggleView(id)} href="">
                                { label }
                            </a>
                        </li>
                    {/each}
                </ul>
            </div>

            <div class="ml-4 mr-4 modal-main-wrapper" class:pb-4={ currentViewId==="main" }>
                <svelte:component this={viewComponents[currentViewId] || null} {...viewProps[currentViewId] || {}}/>
            </div>

        </div>

        {#if canNavigate}
            <button class="nav-btn nav-right" on:click={() => navigate(1)}>
                <span class="icon"><i class="fas fa-chevron-right"/></span>
            </button>
        {/if}
    </div>
    <button on:click={onClose} class="modal-close is-large" aria-label="close"/>
</div>

<style>
    .modal-content {
        width: 80vw;
        height: 80vh;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .nav-btn {
        color: var(--bulma-link);
        cursor: pointer;
        z-index: 1;
        /*width: 3rem;*/
        /*height: 3rem;*/
        /*cursor: pointer;*/
        /*display: flex;*/
        /*align-items: center;*/
        /*justify-content: center;*/
        /*flex-shrink: 0;*/
    }
    .modal-inner {
        flex: 1;
        height: 100%;
        display: grid;
        grid-template-columns: 100%;
        grid-template-rows: 10% 90%;
        background-color: var(--bulma-body-background-color);
        border: var(--default-border);
        border-radius: 1rem;
        overflow: scroll;
    }
    .modal-main-wrapper {
        height: 100%;
    }
</style>

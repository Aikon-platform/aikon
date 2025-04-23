<!--
    general functionning:
    - different components are displayed depending on the context in which this component is used:
        - for "normal" regions, only ModalRegion will be used
        - for similarities, `ModalRegion`, `ModalSimilarity`, `ModalQueryExpansion` will be used
    - `allowedViewIds` defines which views (aka, components) can be used in this modal, based on the props passed to it. each view is identified by a unique string.
    - `currentViewId` is a value of `allowedViewIds`
    - other data variables are derived from `allowedViewIds`: they are objects or arrays which contain and a reference to a value of `allowedViewIds` and extra data for a specific view (i.e. a component reference).
    - tabs allow to switch between components. internally, `toggleView` will set a new `currentViewId`, which, by side-effect, will render a new component
-->
<script>
    import { onMount, onDestroy, createEventDispatcher } from "svelte";

    import { appLang } from "../../constants.js";

    import ModalRegion from "./ModalRegion.svelte";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */
    /** @typedef {"main"|"similarity"|"expansion"} ViewIdType */

    //////////////////////////////////////////////////

    export let mainImg;
    export let compareImg;

    /** @type {RegionItemType} */
    export let mainImgItem;
    /** @type {RegionItemType} */
    export let compareImgItem;

    const dispatch = createEventDispatcher();

    /** @type {ViewIdType[]} */
    const allowedViewIds =
        compareImg || compareImgItem
        ? [ "main", "similarity", "expansion" ]
        : [ "main" ];

    /** @type { {id:ViewIdType, label:string}[] } */
    const viewTabs = allowedViewIds.map((viewId) => ({
        id: viewId,
        label:
            viewId==="expansion" && appLang==="fr"
            ? "Expansion de requête"
            : viewId==="expansion" && appLang==="en"
            ? "Query expansion"
            : viewId==="similarity" && appLang==="fr"
            ? "Similarité"
            : viewId==="similarity" && appLang==="en"
            ? "Similarity"
            : viewId==="main" && appLang==="fr"
            ? "Vue principale"
            : "Main view"
    }));

    /**
     * @type {{ [ViewIdType]: SvelteComponent }} viewId mapped to the relevant component instance.
     * by default, only ModalRegion is defined. other components qre imported aynchronously, after which viewComponents is updated
     */
    const viewComponents = { main: ModalRegion };
    if ( compareImg || compareImgItem ) {
        Promise.all([
            import("./ModalSimilarity.svelte"),
            import("./ModalQueryExpansion.svelte"),
        ]).then(([resModalSimilarity, resModalQueryExpansion]) => {
            let ModalSimilarity = resModalSimilarity.default;
            let ModalQueryExpansion = resModalQueryExpansion.default;
            allowedViewIds.map((viewId) =>
                viewComponents[viewId] =
                    viewId==="expansion"
                    ? ModalQueryExpansion
                    : viewId==="similarity"
                    ? ModalSimilarity
                    : ModalRegion
            );
        })
    }

    const viewProps = {};
    allowedViewIds.map((viewId) =>
        viewProps[viewId] =
            viewId==="expansion"
            ? {compareImg: compareImg, mainImg: mainImg}
            : viewId==="similarity"
            ? {compareImgItem: compareImgItem, mainImgItem: mainImgItem}
            : {mainImgItem: mainImgItem}// {mainImg: mainImg}
    )
    console.log(viewProps);

    /** @type {ViewIdType} */
    $: currentViewId = allowedViewIds[0];

    //////////////////////////////////////////////////

    const toggleView = (viewId) => currentViewId = viewId;

    const onKeyDown = (e) => { if (key==="Escape") dispatch("closeModal") };

    const onClose = (e) => dispatch("closeModal");

    //////////////////////////////////////////////////

    onMount(() => {
        document.addEventListener("keyup", onKeyDown);
    })
    onDestroy(() => {
        document.removeEventListener("keydown", onKeyDown);
    })
</script>


<div id="region-modal-wrapper"
     class="modal is-active">
    <div class="modal-background"></div>
    <div class="modal-content">
        <div class="modal-inner">

            <div class="tabs is-centered">
                <ul>
                    {#each viewTabs as { id, label }}
                        <li class={id===currentViewId ? "is-active": ""}>
                            <!-- svelte-ignore a11y-invalid-attribute -->
                            <a on:click|preventDefault={() => toggleView(id)}
                               href=""
                            >{ label }</a>
                        </li>
                    {/each}
                </ul>
            </div>

            <div class="ml-4 mr-4 modal-main-wrapper"
                 class:pb-4={ currentViewId==="main" }
            >
                <svelte:component this={viewComponents[currentViewId] || null}
                                  {...viewProps[currentViewId] || {}}
                ></svelte:component>
            </div>

        </div>
    </div>
    <button class="modal-close is-large"
            aria-label="close"
            on:click={onClose}
    ></button>
</div>

<style>
    .modal-content {
        width: 80vw;
        height: 80vh;
    }
    .modal-inner {
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

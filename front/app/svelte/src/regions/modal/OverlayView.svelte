<script>
    import { appLang } from "../../constants.js";
    import { refToIIIF } from "../../utils.js";
    import InputSlider from "../../ui/InputSlider.svelte";
    import InputDropdown from "../../ui/InputDropdown.svelte";

    /** @typedef {import("./types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let queryItem;
    /** @type {RegionItemType} */
    export let similarItem;

    const flipChoices = [
        { value: "h", label: appLang === "fr" ? "Basculer horizontalement" : "Flip horizontally" },
        { value: "v", label: appLang === "fr" ? "Basculer verticalement" : "Flip vertically" },
        { value: "hv", label: appLang === "fr" ? "Basculer H+V" : "Flip H+V" }
    ];

    let overlayOpacity = 0.5;
    let overlayRotation = 0;
    let overlayScale = 100;
    let overlayFlip = [1, 1];
    let overlayTranslate = [0, 0];
    let currentlyResetting = false;

    $: queryUrl = refToIIIF(queryItem.img, queryItem.xywh?.join(",") || "full", "full");
    $: similarUrl = refToIIIF(similarItem.img, similarItem.xywh?.join(",") || "full", "full");

    $: cssTransforms = `translate(${overlayTranslate[0] - 50}%, ${overlayTranslate[1]}%)
                        rotate(${overlayRotation}deg)
                        scale(${overlayFlip.map(x => x * (overlayScale / 100)).join()})`;

    const updateFlip = (e) => {
        const flip = e.detail[0];
        overlayFlip = flip === "hv" ? [-1, -1] : flip === "h" ? [-1, 1] : flip === "v" ? [1, -1] : [1, 1];
    };

    const reset = () => {
        overlayOpacity = 0.5;
        overlayRotation = 0;
        overlayScale = 100;
        overlayFlip = [1, 1];
        overlayTranslate = [0, 0];
        currentlyResetting = true;
        setTimeout(() => currentlyResetting = false, 300);
    };
</script>

<div class="similarity-overlay-wrapper">
    <div class="toolbar-wrapper is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
        <div class="toolbar">
            <div class="toolbar-title mt-0 mb-2">
                <strong>{appLang === "en" ? "Query image transformation" : "Modification de l'image requête"}</strong>
            </div>
            <div class="toolbar-controls is-flex is-flex-direction-column is-align-items-start is-justify-content-center">
                <InputSlider minVal={0} maxVal={1} start={0.5} emitOnUpdate={true}
                             title={appLang === "fr" ? "Opacité" : "Opacity"}
                             on:updateSlider={(e) => overlayOpacity = e.detail}/>

                <InputSlider minVal={0} maxVal={360} start={0} step={1} emitOnUpdate={true}
                             title="Rotation"
                             on:updateSlider={(e) => overlayRotation = e.detail}/>

                <InputSlider minVal={0} maxVal={200} start={100} step={1} emitOnUpdate={true}
                             title={appLang === "fr" ? "Redimensionner" : "Scale"}
                             on:updateSlider={(e) => overlayScale = e.detail}/>

                <InputSlider minVal={-100} maxVal={100} start={0} step={1} emitOnUpdate={true}
                             title={appLang === "fr" ? "Translation horizontale" : "Horizontal translate"}
                             on:updateSlider={(e) => overlayTranslate = [e.detail, overlayTranslate[1]]}/>

                <InputSlider minVal={-100} maxVal={100} start={0} step={1} emitOnUpdate={true}
                             title={appLang === "fr" ? "Translation verticale" : "Vertical translate"}
                             on:updateSlider={(e) => overlayTranslate = [overlayTranslate[0], e.detail]}/>

                <InputDropdown choicesItems={flipChoices} start={[]} lightDisplay={true}
                               placeholder={appLang === "fr" ? "Sélectionner" : "Select"}
                               title={appLang === "fr" ? "Basculer" : "Flip"}
                               on:updateValues={updateFlip}/>

                <div class="mt-2 is-flex is-flex-direction-column is-justify-content-center is-align-items-flex-end">
                    <button class="button is-link" on:click={reset}>
                        {appLang === "fr" ? "Réinitialiser" : "Reset"}
                    </button>
                </div>
            </div>
        </div>
    </div>
    <div class="overlay-wrapper">
        <img class="compare-img" src={similarUrl} alt={similarItem.title}/>
        <img class="main-img" class:overlay-reset={currentlyResetting}
             src={queryUrl} alt={queryItem.title} style:opacity={overlayOpacity} style:transform={cssTransforms}/>
    </div>
</div>

<style>
    .similarity-overlay-wrapper {
        display: grid;
        grid-template-columns: max(230px, 25%) min(calc(100% - 230px), 75%);
        grid-template-rows: 100%;
    }
    .toolbar-wrapper {
        padding-right: 1rem;
        border-right: var(--default-border);
    }
    .toolbar {
        min-width: 200px;
        width: 100%;
    }
    .toolbar-title {
        width: 100%;
    }
    .toolbar-controls > :global(*) {
        width: 100%;
    }
    .overlay-wrapper {
        position: relative;
        height: 100%;
        overflow: auto;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-left: 1rem;
    }
    .overlay-wrapper img {
        position: absolute;
        left: 50%;
        transform: translate(-50%, 0);
        max-height: 90%;
        max-width: 90%;
        object-fit: contain;
    }
    .overlay-reset {
        transition: opacity .3s ease-out, transform .3s ease-out;
    }
</style>

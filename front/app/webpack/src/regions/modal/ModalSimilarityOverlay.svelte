<script>
    import { appLang } from "../../constants.js";
    import { setContext } from 'svelte';
    import { writable } from 'svelte/store';

    import InputDropdown from "../../ui/InputDropdown.svelte";
    import InputSlider from "../../ui/InputSlider.svelte";

    /** @typedef {import("../../ui/InputDropdown.svelte").DropdownChoiceArray} DropdownChoiceArray */
    /** @typedef {import("./types.js").SimilarityImgDataType} SimilarityImgDataType */

    /////////////////////////////////////////////

    /** @type {SimilarityImgDataType} */
    export let imgData;

    /** @type {DropdownChoiceArray} */
    const flipChoices = [
        { value:"h", label: appLang==="fr" ? "Basculer horizontalement" : "Flip horizontally" },
        { value:"v", label: appLang==="fr" ? "Basculer verticalement" : "Flip vertically" },
        { value:"hv", label: appLang==="fr" ? "Basculer horizontalement et verticalement" : "Flip horizontally and vertically" }
    ]

    /** @type {number} 0..1 */
    let overlayOpacity = 0.5;
    const startOverlayOpacity = overlayOpacity;

    /** @type {number} 0..360 */
    let overlayRotation = 0;
    const startOverlayRotation = overlayRotation;

    /** @type {number} 0..200. css uses 0..1 values, but to make things more readable we use a 0..200% scale */
    let overlayScale = 100
    const startOverlayScale = overlayScale;

    /** @type {number[]} [0..2, 0..2] X/Y values for css `scale` to perform a flip. will be combined with overlayScale */
    let overlayFlip = [1,1];
    const startOverlayFlip = structuredClone(overlayFlip);

    /** @type{number[]} [-100..100, -100..100] */
    let overlayTranslate = [0,0];
    const startOverlayTranslate = structuredClone(overlayTranslate);

    let currentlyResetting = false;

    /** @type {writable} set a new value to trigger an update in descendant form components that implement this behaviour */
    const resetTrigger = writable(window.crypto.randomUUID());
    setContext("resetTrigger", resetTrigger);

    $: cssTransforms = `translate(${overlayTranslate[0]-50}%, ${overlayTranslate[1]}%)
                        rotate(${overlayRotation}deg)
                        scale(${overlayFlip.map((x) => x * (overlayScale/100)).join()})`;

    /////////////////////////////////////////////

    const makeAlt = (title) => appLang==="fr"
        ? `Vue principale de la région ${title}`
        : `Main view of region ${title}`;

    const updateOverlayOpacity = (e) => overlayOpacity = e.detail;

    const updateOverlayRotation = (e) => overlayRotation = e.detail;

    const updateOverlayScale = (e) => overlayScale = e.detail;

    // reassignment is necessary to redefine `cssTransforms`
    const updateOverlayTranslateX = (e) => overlayTranslate = [ e.detail, overlayTranslate[1] ];

    const updateOverlayTranslateY = (e) => overlayTranslate = [ overlayTranslate[0], e.detail ];

    const updateOverlayFlip = (e) => {
        let flip = e.detail[0];
        overlayFlip =
            flip === "hv"
            ? [-1,-1]
            : flip === "h"
            ? [-1, 1]
            : flip === "v"
            ? [1,-1]
            : [1,1];
    }

    const resetOverlayParams = () => {
        overlayOpacity = startOverlayOpacity;
        overlayRotation = startOverlayRotation;
        overlayScale = startOverlayScale;
        overlayFlip = startOverlayFlip;
        overlayTranslate = startOverlayTranslate;
        // forme elements will be reset
        resetTrigger.set(window.crypto.randomUUID());
        // will set a css class which will animate resetting.
        currentlyResetting = true;
        setTimeout(() => currentlyResetting = false, 1000);
    }
</script>

<div class="similarity-overlay-wrapper">
    <div class="toolbar-wrapper is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
        <div class="toolbar">
            <div class="toolbar-title mt-0 mb-2">
                <strong>Transform query image</strong>
            </div>
            <div class="toolbar-controls is-flex is-flex-direction-column is-align-items-start is-justify-content-center">
                <div class="">
                    <InputSlider minVal={0}
                                maxVal={1}
                                start={startOverlayOpacity}
                                emitOnUpdate={true}
                                title={appLang==="fr" ? "Opacité" : "Opacity"}
                                on:updateSlider={updateOverlayOpacity}
                    ></InputSlider>
                </div>
                <div class="">
                    <InputSlider minVal={0}
                                maxVal={360}
                                start={startOverlayRotation}
                                step={1}
                                emitOnUpdate={true}
                                title="Rotation"
                                on:updateSlider={updateOverlayRotation}
                    ></InputSlider>
                </div>
                <div class="">
                    <InputSlider minVal={0}
                                maxVal={200}
                                step={1}
                                start={startOverlayScale}
                                emitOnUpdate={true}
                                title={appLang==="fr" ? "Redimensionner" : "Scale"}
                                on:updateSlider={updateOverlayScale}
                    ></InputSlider>
                </div>
                <div class="">
                    <InputSlider minVal={-100}
                                maxVal={100}
                                step={1}
                                start={startOverlayTranslate[0]}
                                emitOnUpdate={true}
                                title={appLang==="fr" ? "Translation horizontale" : "Horizontal translate"}
                                on:updateSlider={updateOverlayTranslateX}
                    ></InputSlider>
                </div>
                <div class="">
                    <InputSlider minVal={-100}
                                maxVal={100}
                                step={1}
                                start={startOverlayTranslate[1]}
                                emitOnUpdate={true}
                                title={appLang==="fr" ? "Translation verticale" : "Vertical translate"}
                                on:updateSlider={updateOverlayTranslateY}
                    ></InputSlider>
                </div>
                <div class="">
                    <InputDropdown choicesItems={flipChoices}
                                start={[]}
                                lightDisplay={true}
                                placeholder={appLang==="fr" ? "Séléctionner" : "Select"}
                                title={appLang==="fr" ? "Basculer" : "Flip"}
                                on:updateValues={updateOverlayFlip}
                    ></InputDropdown>
                </div>
                <div class="mt-2 is-flex is-flex-direction-column is-justify-content-center is-align-items-flex-end">
                    <button class="button is-link"
                            on:click={resetOverlayParams}
                    >{appLang==="fr" ? "Réinitialiser" : "Reset"}</button>
                </div>
            </div>
        </div>
    </div>
    <div class="overlay-wrapper">
        <img class="compare-img"
             src={imgData.queryImage.href}
             alt={imgData.queryImage.title}
        >
        <img class="main-img"
             class:overlay-reset={currentlyResetting}
             src={imgData.similarityImage.href}
             alt={imgData.similarityImage.title}
             style:opacity={overlayOpacity}
             style:transform={cssTransforms}
        >
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
    .toolbar-controls > * {
        width: 100%;
    }
    .overlay-wrapper {
        position: relative;
        height: 100%;
        overflow: scroll;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-left: 1rem;
    }
    .overlay-wrapper img {
        position: absolute;
        left: 50%;
        transform: translate(-50%, 0);
    }
    .overlay-reset {
        transition: opacity .3s ease-out, transform .3s ease-out;
    }
</style>

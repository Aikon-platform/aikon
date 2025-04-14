<script>
    import { refToIIIF } from "../../utils";
    import { appLang } from "../../constants.js";

    import InputToggleCheckbox from "../../ui/InputToggleCheckbox.svelte";
    import InputDropdown from "../../ui/InputDropdown.svelte";
    import InputSlider from "../../ui/InputSlider.svelte";

    /** @typedef {import("../../ui/InputDropdown.svelte").DropdownChoiceArray} DropdownChoiceArray */

    /////////////////////////////////////////////

    /** @type {string} */
    export let mainImg;
    /** @type {string} */
    export let compareImg;

    /** @type {boolean} */
    let overlay = false;

    /** @type {number} 0..1 */
    let overlayOpacity = 0;

    /** @type {number} 0..360 */
    let overlayRotation = 0;

    let overlayFlip = "";

    const mainImgHref = refToIIIF(mainImg);
    const compareImgHref = refToIIIF(compareImg);

    /** @type {DropdownChoiceArray} */
    const flipChoices = [
        { value:"n", label: "Normal" },
        { value:"h", label: appLang==="fr" ? "Basculer horizontalement" : "Flip horizontally" },
        { value:"v", label: appLang==="fr" ? "Basculer verticalement" : "Flip vertically" },
        { value:"hv", label: appLang==="fr" ? "Basculer horizontalement et verticalement" : "Flip horizontally and vertically" }
    ]

    /////////////////////////////////////////////

    //TODO find way to combine styles together

    const updateToggleOverlay = () => overlay = !overlay;

    const updateOverlayOpacity = (e) => overlayOpacity = e.detail;

    const updateOverlayRotation = (e) => overlayRotation = e.detail;

    const updateOverlayFlip = (e) => overlayFlip =
        e.detail === "hv"
        ? "scale(-1,-1)"
        : e.detail === "h"
        ? "scaleX(-1)"
        : e.detail === "v"
        ? "scaleY(-1)"
        : "scale(0,0)";

    const makeAlt = (title) => appLang==="fr"
        ? `Vue principale de la région ${title}`
        : `Main view of region ${title}`;
</script>

<div>
    <div>
        {#if !overlay}
            <div class="columns">
                {#each [[compareImg, compareImgHref], [mainImg, mainImgHref]] as [imgTitle, imgHref], i}
                    <div class="column is-flex is-flex-direction-column is-justify-content-center is-align-items-center">
                        <span>{
                            i===0 && appLang==="fr"
                            ? "Image requête"
                            : i===1 && appLang==="fr"
                            ? "Similarité"
                            : i===0 && appLang==="en"
                            ? "Query image"
                            : "Similarity"
                        }</span>
                        <img src={imgHref}
                             alt={makeAlt(imgTitle)}
                        >
                    </div>
                {/each}
            </div>
        {:else}
            <div>
                <div class="overlay-wrapper">
                    <img src={compareImgHref}
                         alt={makeAlt(compareImg)}>
                    <img src={mainImgHref}
                         alt={makeAlt(mainImg)}
                         style:opacity={overlayOpacity}
                         style:transform={`translate(-50%, 0) rotate(${overlayRotation}deg)`}
                    >
                </div>
                <div class="toolbar-wrapper columns">
                    <div class="column is-one-third">
                        <InputSlider minVal={0}
                                    maxVal={1}
                                    start={0}
                                    emitOnUpdate={true}
                                    title={appLang==="fr" ? "Opacité de l'image requête" : "Query image opacity"}
                                    on:updateSlider={updateOverlayOpacity}
                        ></InputSlider>
                    </div>
                    <div class="column is-one-third">
                        <InputSlider minVal={0}
                                    maxVal={360}
                                    start={0}
                                    step={1}
                                    emitOnUpdate={true}
                                    title={appLang==="fr" ? "Rotation de l'image requête" : "Query image rotation"}
                                    on:updateSlider={updateOverlayRotation}
                        ></InputSlider>
                    </div>
                    <div class="column is-one-third">
                        <InputDropdown choicesItems={flipChoices}
                                       start={["n"]}
                                       lightDisplay={true}
                                       placeholder="..."
                                       title={appLang==="fr" ? "Basculer l'image" : "Flip image"}
                                       on:updateValues={updateOverlayFlip}
                        ></InputDropdown>
                    </div>
                </div>
            </div>
        {/if}
    </div>
    <div>
        <InputToggleCheckbox start={false}
                             buttonDisplay={true}
                             checkboxLabel={appLang==="en" ? "Overlay view" : "Vue superposée"}
                             on:updateChecked={updateToggleOverlay}
        ></InputToggleCheckbox>
    </div>
</div>

<style>
    img {
        object-fit: contain;
        max-height: 80%;
        max-width: 80%;
    }
    .overlay-wrapper {
        position: relative;
        min-height: 50vh;  /** dirty */
    }
    .overlay-wrapper img {
        position: absolute;
        left: 50%;
        transform: translate(-50%, 0);
    }
</style>

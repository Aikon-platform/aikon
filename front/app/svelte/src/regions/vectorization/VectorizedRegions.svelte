<script>
    import { run, createBubbler } from 'svelte/legacy';

    const bubble = createBubbler();
    import { fade } from "svelte/transition";
    import { onMount, onDestroy } from "svelte";
    import { appLang, mediaPrefix } from "../../constants.js";
    import { refToIIIF } from "../../utils.svelte.js";

    /**
     * @typedef {Object} Props
     * @property {any} svgPath
     * @property {number} [width]
     * @property {boolean} [fullWidth]
     * @property {boolean} [selected]
     * @property {import('svelte').Snippet} [actions]
     */

    /** @type {Props} */
    let {
        svgPath,
        width = 200,
        fullWidth = false,
        selected = false,
        actions
    } = $props();

    const [wit, digit, canvas, xywh] = svgPath.replace(".svg", "").split("_");
    const img = refToIIIF(`${wit}_${digit}_${canvas}`, xywh, `${width},`);

    let isHovered = $state(false);
    let svgContent = $state("");
    let svgViewBox = $state("");
    let downloadUrl = $state("");

    run(() => {
        if (svgContent) {
            const blob = new Blob([svgContent], { type: "image/svg+xml" });
            downloadUrl = URL.createObjectURL(blob);
        }
    });

    onDestroy(() => {
        if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    });

    onMount(async () => {
        const response = await fetch(`${mediaPrefix}svg/${svgPath}`);
        const svgText = await response.text();

        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(svgText, "image/svg+xml");

        const svgElement = svgDoc.querySelector("svg");
        svgViewBox = svgElement.getAttribute("viewBox") || `0 0 ${svgElement.getAttribute("width")} ${svgElement.getAttribute("height")}`;

        svgDoc.querySelectorAll("image").forEach(img => img.remove());

        svgElement.setAttribute("viewBox", svgViewBox);
        svgElement.removeAttribute("width");
        svgElement.removeAttribute("height");

        svgContent = new XMLSerializer().serializeToString(svgDoc.documentElement);
    });
</script>

<div class="region is-center" class:checked={selected} transition:fade|global={{ duration: 300 }}>
    <figure class="image card region-image" style="width: {fullWidth ? '50%' : `${width}px`}; aspect-ratio:{svgViewBox ? svgViewBox.split(' ')[2] / svgViewBox.split(' ')[3] : 1};"
            onclick={bubble('click')} onkeyup={bubble('keyup')} onmouseenter={() => isHovered = true} onmouseleave={() => isHovered = false}>
        <div class="svg-container">
            {#if !isHovered && svgContent}
                {@html svgContent}
            {/if}
        </div>
        <img class="region-img" src="{img}" alt="Extracted region"/>
    </figure>

    <div class="region-btn ml-1">
        <a class="button tag" href={downloadUrl} download={svgPath}>
            <i class="fa-solid fa-download"></i>
            <span class="tooltip">{appLang === "en" ? "Download SVG" : "Télécharger le SVG"}</span>
        </a>
        {@render actions?.()}
    </div>
</div>

<style>
    .svg-container {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
    }

    .svg-container :global(svg) {
        width: 100%;
        height: 100%;
    }

    .region-image {
        max-height: 100%;
    }

    .svg-container,
    .region-img {
        height: 100%;
        width: auto;
        object-fit: contain;
    }

    .button {
        padding-left: .8em;
        padding-right: .2em;
        color: var(--bulma-link);
    }
</style>

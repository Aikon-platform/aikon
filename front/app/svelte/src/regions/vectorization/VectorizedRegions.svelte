<script>
    import { fade } from 'svelte/transition';
    import { onMount, onDestroy } from 'svelte';
    import { appLang, mediaPrefix } from "../../constants.js";
    import { refToIIIF } from "../../utils.js";

    export let svgPath;
    export let width = 200;
    export let fullWidth = false;
    export let selected = false;

    const [wit, digit, canvas, xywh] = svgPath.replace(".svg", "").split("_");
    const img = refToIIIF(`${wit}_${digit}_${canvas}`, xywh, `${width},`);

    let isHovered = false;
    let svgContent = '';
    let svgViewBox = '';
    let downloadUrl = '';

    $: if (svgContent) {
        const blob = new Blob([svgContent], { type: "image/svg+xml" });
        downloadUrl = URL.createObjectURL(blob);
    }

    onDestroy(() => {
        if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    });

    onMount(async () => {
        const response = await fetch(`${mediaPrefix}svg/${svgPath}`);
        const svgText = await response.text();

        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(svgText, 'image/svg+xml');

        const svgElement = svgDoc.querySelector('svg');
        svgViewBox = svgElement.getAttribute('viewBox') || `0 0 ${svgElement.getAttribute('width')} ${svgElement.getAttribute('height')}`;

        svgDoc.querySelectorAll('image').forEach(img => img.remove());

        svgElement.setAttribute('viewBox', svgViewBox);
        svgElement.removeAttribute('width');
        svgElement.removeAttribute('height');

        svgContent = new XMLSerializer().serializeToString(svgDoc.documentElement);
    });
</script>

<div class="region is-center" class:checked={selected} transition:fade={{ duration: 300 }}>
    <figure class="image card region-image" style="width: {fullWidth ? '50%' : `${width}px`}; aspect-ratio:{svgViewBox ? svgViewBox.split(' ')[2] / svgViewBox.split(' ')[3] : 1};"
            on:click on:keyup on:mouseenter={() => isHovered = true} on:mouseleave={() => isHovered = false}>
        <div class="svg-container">
            {#if !isHovered && svgContent}
                {@html svgContent}
            {/if}
        </div>
        <img class="region-img" src="{img}" alt="Extracted region"/>
    </figure>

    <div class="region-btn ml-1">
        <a class="button tag" href={downloadUrl} download={svgPath}>
            <i class="fa-solid fa-download"/>
            <span class="tooltip">{appLang === 'en' ? "Download SVG" : "Télécharger le SVG"}</span>
        </a>
        <slot name="actions"/>
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

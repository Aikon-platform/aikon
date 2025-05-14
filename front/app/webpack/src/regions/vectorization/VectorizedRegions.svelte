<script>
    import { fade } from 'svelte/transition';
    import { onMount } from 'svelte';
    import {mediaPrefix } from "../../constants.js";
    import {refToIIIF} from "../../utils.js";

    export let svgPath;
    export let width = 200;
    const [wit, digit, canvas, xywh] = svgPath.replace(".svg", "").replace(".jpg", "").split("_");
    const img = refToIIIF(`${wit}_${digit}_${canvas}`, xywh, `${width},`);

    let isHovered = false;
    let svgContent = '';
    let svgViewBox = '';

    // TODO display name and canvas of the region
    // TODO add button to access individual vectorization
    // TODO add button to delete svg

    onMount(async () => {
        const response = await fetch(`${mediaPrefix}svg/${svgPath}`);
        const svgText = await response.text();

        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(svgText, 'image/svg+xml');

        // Get the viewBox
        const svgElement = svgDoc.querySelector('svg');
        svgViewBox = svgElement.getAttribute('viewBox') || `0 0 ${svgElement.getAttribute('width')} ${svgElement.getAttribute('height')}`;

        svgDoc.querySelectorAll('image').forEach(img => img.remove());

        // Ensure the SVG has a viewBox
        svgElement.setAttribute('viewBox', svgViewBox);
        // Remove width and height attributes to allow proper scaling
        svgElement.removeAttribute('width');
        svgElement.removeAttribute('height');

        svgContent = new XMLSerializer().serializeToString(svgDoc.documentElement);
    });
</script>

<div class="svg-regions is-center" transition:fade={{ duration: 500 }}
     on:mouseenter={() => isHovered = true} on:mouseleave={() => isHovered = false}>
    <figure class="image card region-image" style="width: {width}px; aspect-ratio: {svgViewBox ? svgViewBox.split(' ')[2] / svgViewBox.split(' ')[3] : 1};">
        <div class="svg-container">
            {#if !isHovered && svgContent}
                {@html svgContent}
            {/if}
        </div>
        <img src="{img}" alt="Extracted region"/>
    </figure>
</div>

<style>
    .svg-regions {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
    }

    .image {
        position: relative;
        width: 100%;
        height: 100%;
    }

    .svg-container {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }

    .svg-container :global(svg) {
        width: 100%;
        height: 100%;
    }

    img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
</style>

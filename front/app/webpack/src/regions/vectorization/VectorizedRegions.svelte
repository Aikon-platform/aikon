<script>
    import { fade } from 'svelte/transition';
    import { onMount, getContext } from 'svelte';

    import { mediaPrefix } from "../../constants.js";
    import { refToIIIF } from "../../utils.js";

    import { selectionStore } from "../../selection/selectionStore.js";
    const { isSelected } = selectionStore;

    import { regionsStore } from "../../regions/regionsStore.js";
    const { clipBoard } = regionsStore;

    export let svgPath;
    export let width = 200;
    export let fullWidth = false;
    export let selectable = true;

    const [wit, digit, canvas, xywh] = svgPath.replace(".svg", "").split("_");
    const img = refToIIIF(`${wit}_${digit}_${canvas}`, xywh, `${width},`);

    let isHovered = false;
    let svgContent = '';
    let svgViewBox = '';

    const compareImgItem = getContext("qImgMetadata") || undefined;
    const isInModal = getContext("isInModal") || false;
    const transitionDuration = isInModal ? 0 : 500;

    let modalControllerComponent;
    if ( !isInModal ) {
        import("../modal/ModalController.svelte").then((res) => modalControllerComponent = res.default);
    }

    let item = {
        ref: svgPath,
        img: `${wit}_${digit}_${canvas}`,
        xywh
    };

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

<div class="region is-center {selectable && $isSelected(item) ? 'checked' : ''}"
    transition:fade={{ duration: transitionDuration }}
>
    <figure class="image card region-image"
        style="
            width: {fullWidth ? '50%' : `${width}px`};
            aspect-ratio:{svgViewBox ? svgViewBox.split(' ')[2] / svgViewBox.split(' ')[3] : 1};
        "
        on:click={() => selectable ? selectionStore.toggle(item) : null}
        on:mouseenter={() => isHovered = true}
        on:mouseleave={() => isHovered = false}
    >
        <div class="svg-container">
            {#if !isHovered && svgContent}
                {@html svgContent}
            {/if}
        </div>
        <img class="region-img" src="{img}" alt="Extracted region"/>
    </figure>

    <div class="region-btn ml-1">
        {#if modalControllerComponent}
            <svelte:component this={modalControllerComponent}
                mainImgItem={item}
                compareImgItem={compareImgItem}
                svgItem={svgPath}
            />
        {/if}
    </div>
</div>

<style>
    .region {
        cursor: pointer;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: start;
        max-height: 100%;
    }

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

    .region-btn {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-around;
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
</style>

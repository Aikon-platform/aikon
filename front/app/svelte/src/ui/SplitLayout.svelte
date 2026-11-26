<!-- @migeation-task-ok -->
<!-- @migration-task Error while migrating Svelte code: `$:` is not allowed in runes mode, use `$derived` or `$effect` instead
https://svelte.dev/e/legacy_reactive_statement_invalid -->
<script>
    import {onDestroy, onMount} from "svelte";

    let { leftTitle, leftScroll, bottomLeftTitle, bottomLeftScroll, rightTitle, rightScroll, bottomRightTitle, bottomRightScroll } = $props();

    const MIN_WIDTH = 250;
    const MIN_HEIGHT = 100;
    let container;
    let resizeObserver;
    let hRatio = 0.5;  // horizontal
    let vRatio = 0.5;  // vertical
    let dragging = null; // 'h' | 'v' | null
    let containerWidth = 0;
    let rightPanelHeight = 0;
    let leftPanelHeight = 0;
    let rightPanel;
    let leftPanel;

    let leftWidth = $state(Math.max(MIN_WIDTH, containerWidth * hRatio - 4));
    let rightWidth = $state(Math.max(MIN_WIDTH, containerWidth * (1 - hRatio) - 4));

    let hasBottomLeft = $derived(!!(bottomLeftTitle || bottomLeftScroll));
    let hasBottomRight = $derived(!!(bottomRightTitle || bottomRightScroll));

    let rightTopHeight = $state(Math.max(MIN_HEIGHT, rightPanelHeight * vRatio - 4));
    let rightBottomHeight = $state(Math.max(MIN_HEIGHT, rightPanelHeight * (1 - vRatio) - 4));
    let leftTopHeight = $state(Math.max(MIN_HEIGHT, leftPanelHeight * vRatio - 4));
    let leftBottomHeight = $state(Math.max(MIN_HEIGHT, leftPanelHeight * (1 - vRatio) - 4));

    function startDrag(axis) {
        return (e) => {
            dragging = axis;
            e.preventDefault();
        };
    }

    function onDrag(e) {
        if (!dragging) return;
        const clientX = e.clientX ?? e.touches?.[0]?.clientX;
        const clientY = e.clientY ?? e.touches?.[0]?.clientY;

        if (dragging === "h" && container) {
            const rect = container.getBoundingClientRect();
            hRatio = Math.max(0.2, Math.min(0.8, (clientX - rect.left) / rect.width));
        } else if (dragging === "v" && rightPanel) {
            const panel = rightPanel || leftPanel;
            if (!panel) return;
            const rect = panel.getBoundingClientRect();
            vRatio = Math.max(0.2, Math.min(0.8, (clientY - rect.top) / rect.height));
        }
    }

    function stopDrag() {
        dragging = null;
    }

    onMount(() => {
        if (container) {
            containerWidth = container.offsetWidth;
            resizeObserver = new ResizeObserver(entries => {
                containerWidth = entries[0].contentRect.width;
            });
            resizeObserver.observe(container);
        }
        window.addEventListener("mousemove", onDrag);
        window.addEventListener("mouseup", stopDrag);
        window.addEventListener("touchmove", onDrag);
        window.addEventListener("touchend", stopDrag);
    });

    onDestroy(() => {
        resizeObserver?.disconnect();
        window.removeEventListener("mousemove", onDrag);
        window.removeEventListener("mouseup", stopDrag);
        window.removeEventListener("touchmove", onDrag);
        window.removeEventListener("touchend", stopDrag);
    });

    function observePanel(node, side = "left") {
        const ro = new ResizeObserver(entries => {
            if (side === "left") {
                leftPanelHeight = entries[0].contentRect.height;
            } else {
                rightPanelHeight = entries[0].contentRect.height;
            }

        });
        ro.observe(node);
        if (side === "left") {
            leftPanel = node;
        } else {
            rightPanel = node;
        }
        return { destroy: () => ro.disconnect() };
    }

    function observeRightPanel(node) {
        observePanel(node, "right");
    }

    function observeLeftPanel(node) {
        observePanel(node, "left");
    }
</script>

<div class="split-container" bind:this={container}>
    <div class="split-panel" style="width: {leftWidth}px;" use:observeLeftPanel>
         {#if hasBottomLeft}
            <div class="box panel-box mb-0" style="height: {leftTopHeight}px;">
                <div class="mb-3">{@render leftTitle()}</div>
                <div class="scroll-area">{@render leftScroll()}</div>
            </div>
            <div class="split-divider v" onmousedown={startDrag("v")} ontouchstart={startDrag("v")} role="separator" tabindex="-1"></div>
            <div class="box panel-box" style="height: {leftBottomHeight}px;">
                <div class="mb-3">{@render bottomLeftTitle()}</div>
                <div class="scroll-area">{@render bottomLeftScroll()}</div>
            </div>
        {:else}
            <div class="box panel-box">
                <div class="mb-3">{@render leftTitle()}</div>
                <div class="scroll-area">{@render leftScroll()}</div>
            </div>
        {/if}
    </div>

    <div class="split-divider h" onmousedown={startDrag("h")} ontouchstart={startDrag("h")} role="separator" tabindex="-1"></div>

    <div class="split-panel" style="width: {rightWidth}px;" use:observeRightPanel>
        {#if hasBottomRight}
            <div class="box panel-box mb-0" style="height: {rightTopHeight}px;">
                <div class="mb-3">{@render rightTitle()}</div>
                <div class="scroll-area">{@render rightScroll()}</div>
            </div>
            <div class="split-divider v" onmousedown={startDrag("v")} ontouchstart={startDrag("v")} role="separator" tabindex="-1"></div>
            <div class="box panel-box" style="height: {rightBottomHeight}px;">
                <div class="mb-3">{@render bottomRightTitle()}</div>
                <div class="scroll-area">{@render bottomRightScroll()}</div>
            </div>
        {:else}
            <div class="box panel-box">
                <div class="mb-3">{@render rightTitle()}</div>
                <div class="scroll-area">{@render rightScroll()}</div>
            </div>
        {/if}
    </div>
</div>

<style>
    .split-container {
        display: flex;
        user-select: none;
    }
    .split-panel {
        flex-shrink: 0;
        min-width: 0;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .split-divider {
        position: relative;
        flex-shrink: 0;
    }
    .split-divider.h {
        width: 8px;
        cursor: col-resize;
    }
    .split-divider.v {
        height: 8px;
        cursor: row-resize;
    }
    .split-divider::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--bulma-border);
        border-radius: 2px;
    }
    .split-divider.h::after { width: 4px; height: 40px; }
    .split-divider.v::after { width: 40px; height: 4px; }
    .split-divider:hover::after { background: var(--bulma-link); }
    .panel-box {
        display: flex;
        flex-direction: column;
        flex: 1;
        min-height: 0;
        overflow-x: hidden;
    }
    .scroll-area {
        flex: 1;
        overflow: auto;
    }
</style>

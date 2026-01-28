<script>
    import {onDestroy, onMount} from "svelte";

    const MIN_WIDTH = 250;
    const MIN_HEIGHT = 100;
    let container;
    let resizeObserver;
    let hRatio = 0.5;  // horizontal
    let vRatio = 0.5;  // vertical (for right panel split)
    let dragging = null; // 'h' | 'v' | null
    let containerWidth = 0;
    let rightPanelHeight = 0;
    let rightPanel;

    $: leftWidth = Math.max(MIN_WIDTH, containerWidth * hRatio - 4);
    $: rightWidth = Math.max(MIN_WIDTH, containerWidth * (1 - hRatio) - 4);
    $: topHeight = Math.max(MIN_HEIGHT, rightPanelHeight * vRatio - 4);
    $: bottomHeight = Math.max(MIN_HEIGHT, rightPanelHeight * (1 - vRatio) - 4);
    $: hasBottomRight = $$slots['bottom-right-title'] || $$slots['bottom-right-scroll'];

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

        if (dragging === 'h' && container) {
            const rect = container.getBoundingClientRect();
            hRatio = Math.max(0.2, Math.min(0.8, (clientX - rect.left) / rect.width));
        } else if (dragging === 'v' && rightPanel) {
            const rect = rightPanel.getBoundingClientRect();
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
        window.addEventListener('mousemove', onDrag);
        window.addEventListener('mouseup', stopDrag);
        window.addEventListener('touchmove', onDrag);
        window.addEventListener('touchend', stopDrag);
    });

    onDestroy(() => {
        resizeObserver?.disconnect();
        window.removeEventListener('mousemove', onDrag);
        window.removeEventListener('mouseup', stopDrag);
        window.removeEventListener('touchmove', onDrag);
        window.removeEventListener('touchend', stopDrag);
    });

    function observeRightPanel(node) {
        const ro = new ResizeObserver(entries => {
            rightPanelHeight = entries[0].contentRect.height;
        });
        ro.observe(node);
        rightPanel = node;
        return { destroy: () => ro.disconnect() };
    }
</script>

<div class="split-container" bind:this={container}>
    <div class="split-panel" style="width: {leftWidth}px;">
        <div class="box panel-box">
            <div class="mb-3"><slot name="left-title"/></div>
            <div class="scroll-area"><slot name="left-scroll"/></div>
        </div>
    </div>

    <div class="split-divider h" on:mousedown={startDrag('h')} on:touchstart={startDrag('h')} role="separator" tabindex="-1"/>

    <div class="split-panel" style="width: {rightWidth}px;" use:observeRightPanel>
        {#if hasBottomRight}
            <div class="box panel-box" style="height: {topHeight}px;">
                <div class="mb-3"><slot name="right-title"/></div>
                <div class="scroll-area"><slot name="right-scroll"/></div>
            </div>
            <div class="split-divider v" on:mousedown={startDrag('v')} on:touchstart={startDrag('v')} role="separator" tabindex="-1"/>
            <div class="box panel-box" style="height: {bottomHeight}px;">
                <div class="mb-3"><slot name="bottom-right-title"/></div>
                <div class="scroll-area"><slot name="bottom-right-scroll"/></div>
            </div>
        {:else}
            <div class="box panel-box">
                <div class="mb-3"><slot name="right-title"/></div>
                <div class="scroll-area"><slot name="right-scroll"/></div>
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
    }
    .scroll-area {
        flex: 1;
        overflow: auto;
    }
</style>

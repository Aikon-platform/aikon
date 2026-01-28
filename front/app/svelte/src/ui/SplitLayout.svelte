<script>
    import {onDestroy, onMount} from "svelte";

    const MIN_WIDTH = 250;
    let container;
    let resizeObserver;
    let splitRatio = 0.5;
    let isDragging = false;
    let containerWidth = 0;

    $: leftWidth = Math.max(MIN_WIDTH, containerWidth * splitRatio - 4);
    $: rightWidth = Math.max(MIN_WIDTH, containerWidth * (1 - splitRatio) - 4);

    function startDrag(e) {
        isDragging = true;
        e.preventDefault();
    }

    function onDrag(e) {
        if (!isDragging || !container) return;
        const rect = container.getBoundingClientRect();
        const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
        splitRatio = Math.max(0.2, Math.min(0.8, x / rect.width));
    }

    function stopDrag() {
        isDragging = false;
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
</script>

<div class="split-container" bind:this={container}>
    <div class="split-panel" style="width: {leftWidth}px;">
        <div class="box panel-box">
            <div class="mb-3">
                <slot name="left-title"/>
            </div>
            <div class="scroll-area">
                <slot name="left-scroll"/>
            </div>
        </div>
    </div>

    <div class="split-divider" on:mousedown={startDrag} on:touchstart={startDrag} role="separator" tabindex="-1"/>

    <div class="split-panel" style="width: {rightWidth}px;">
        <div class="box panel-box">
            <div class="mb-3">
                <slot name="right-title"/>
            </div>
            <div class="scroll-area">
                <slot name="right-scroll"/>
            </div>
        </div>
    </div>
</div>

<style>
    .split-container {
        display: flex;
        gap: 0;
        user-select: none;
    }

    .split-panel {
        flex-shrink: 0;
        min-width: 0;
        height: 100%;
    }

    .split-divider {
        width: 8px;
        cursor: col-resize;
        background: transparent;
        position: relative;
        flex-shrink: 0;
    }

    .split-divider::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 4px;
        height: 40px;
        background: var(--bulma-border);
        border-radius: 2px;
    }

    .split-divider:hover::after {
        background: var(--bulma-link);
    }

    .panel-box {
        height: 100%;
        display: flex;
        flex-direction: column;
    }

    .scroll-area {
        flex: 1;
        overflow: auto;
        max-height: calc(100vh - 250px);
    }
</style>

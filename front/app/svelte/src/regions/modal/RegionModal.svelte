<script>
    import { createEventDispatcher, onMount, onDestroy } from "svelte";
    import NavigationArrow from "../../ui/NavigationArrow.svelte";

    export let open = false;
    /** @type {any[]} */
    export let items = [];
    export let currentIndex = 0;

    const dispatch = createEventDispatcher();

    $: canNavigate = items.length > 1;
    $: currentItem = items[currentIndex] ?? null;

    const close = () => {
        open = false;
        dispatch("close");
    };

    const navigate = (delta) => {
        if (!canNavigate) return;
        currentIndex = (currentIndex + delta + items.length) % items.length;
        dispatch("navigate", { index: currentIndex, item: currentItem });
    };

    const onKeydown = (e) => {
        if (!open) return;
        if (e.key === "Escape") close();
        else if (e.key === "ArrowLeft") navigate(-1);
        else if (e.key === "ArrowRight") navigate(1);
    };

    onMount(() => document.addEventListener("keydown", onKeydown));
    onDestroy(() => document.removeEventListener("keydown", onKeydown));
</script>

{#if open}
    <div class="modal is-active">
        <div class="modal-background" on:click={close} on:keyup/>
        <div class="modal-content">
            {#if canNavigate}
                <NavigationArrow direction="left" delta={-1} navigationFct={navigate} css={"position: initial;"}/>
            {/if}

            <div class="modal-inner">
                <slot item={currentItem} index={currentIndex} {close}/>
            </div>

            {#if canNavigate}
                <NavigationArrow direction="right" delta={1} navigationFct={navigate} css={"position: initial;"}/>
            {/if}
        </div>
        <button class="modal-close is-large" on:click={close} aria-label="close"/>
    </div>
{/if}

<style>
    .modal-content {
        width: 80vw;
        height: 80vh;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .modal-inner {
        flex: 1;
        height: 100%;
        display: flex;
        flex-direction: column;
        background-color: var(--bulma-body-background-color);
        border: var(--default-border);
        border-radius: 1rem;
        overflow: auto;
    }
</style>

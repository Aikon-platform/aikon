<script>
    import { createBubbler } from 'svelte/legacy';

    const bubble = createBubbler();
    import { createEventDispatcher, onMount, onDestroy, setContext } from "svelte";
    import { appendToDom } from "../../utils.svelte.js";
    import NavigationArrow from "../../ui/NavigationArrow.svelte";


    /**
     * @typedef {Object} Props
     * @property {boolean} [open]
     * @property {any[]} [items]
     * @property {number} [currentIndex]
     * @property {import('svelte').Snippet<[any]>} [children]
     */

    /** @type {Props} */
    let {
        open = $bindable(false),
        items = [],
        currentIndex = $bindable(0),
        children
    } = $props();

    const dispatch = createEventDispatcher();

    /** @type {any|null} when set, overrides items with a single region */
    let anchor = $state(null);
    setContext("setModalAnchor", (item) => { anchor = item; currentIndex = 0; });

    let activeItems = $derived(anchor ? [anchor] : items);
    let canNavigate = $derived(activeItems.length > 1);
    let currentItem = $derived(activeItems[currentIndex] ?? null);

    const close = () => {
        open = false;
        anchor = null;
        dispatch("close");
    };

    const navigate = (delta) => {
        if (!canNavigate) return;
        currentIndex = (currentIndex + delta + activeItems.length) % activeItems.length;
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
    <div class="modal is-active" use:appendToDom>
        <div class="modal-background" onclick={close} onkeyup={bubble('keyup')}></div>
        <div class="modal-content">
            {#if canNavigate}
                <NavigationArrow direction="left" delta={-1} navigationFct={navigate} css="position: initial;"/>
            {/if}

            <div class="modal-inner">
                <!--<a class="button is-small is-link is-light m-2 is-align-self-flex-end" href={new RegionItem(currentItem).viewUrl} target="_blank">
                    <i class="fa-solid fa-up-right-from-square"/>
                </a>-->
                {@render children?.({ item: currentItem, index: currentIndex, anchored: !!anchor, close, })}
            </div>

            {#if canNavigate}
                <NavigationArrow direction="right" delta={1} navigationFct={navigate} css="position: initial;"/>
            {/if}
        </div>
        <button class="modal-close is-large" onclick={close} aria-label="close"></button>
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

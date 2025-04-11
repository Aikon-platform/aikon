<script>
    import { onMount, onDestroy, createEventDispatcher } from "svelte";

    const dispatch = createEventDispatcher();

    const onKeyDown = (e) => {
        if (key==="Escape") {
            dispatch("closeModal");
        }
    };

    onMount(() => {
        document.addEventListener("keyup", onKeyDown);
    })
    onDestroy(() => {
        document.removeEventListener("keydown", onKeyDown);
    })
</script>


<div id="region-modal-wrapper"
     class="modal is-active">
    <div class="modal-background"></div>
    <div class="modal-content"></div>
    <button class="modal-close is-large" aria-label="close"></button>
</div>

<style>
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
    }
</style>

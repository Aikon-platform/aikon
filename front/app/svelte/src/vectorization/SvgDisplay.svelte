<script>
    import { createEventDispatcher } from 'svelte';

    const dispatcher = createEventDispatcher();

    export let svg

    function handleElementClick(event) {
        if (event.target !== event.currentTarget) {
            dispatcher('elementSelect', event.target);
        }
    }
</script>

<div bind:innerHTML={svg} on:click={handleElementClick} />

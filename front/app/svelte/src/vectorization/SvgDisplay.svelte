
<script>
    let { svg, onelementSelect } = $props();

    function handleElementClick(event) {
        if (event.target !== event.currentTarget) {
            onelementSelect?.(event.target);
        }
    }
</script>

<div onclick={handleElementClick}>{@html svg}</div>

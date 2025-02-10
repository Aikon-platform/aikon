<script>
    import { createEventDispatcher } from 'svelte';

    const dispatcher = createEventDispatcher();

    let color = '';
    let strokeWidth = '';

    const colors = ['red', 'green', 'blue', 'yellow', 'black'];
    const strokeWidths = ['1', '2', '3', '4', '5'];

    function updateColor(event) {
        dispatcher('updateElement', { property: 'stroke', value: event.target.value });
    }

    function updateStrokeWidth(event) {
        dispatcher('updateElement', { property: 'stroke-width', value: event.target.value });
    }

    function deleteElement() {
        dispatcher('updateElement', { property: 'remove' });
    }
</script>

<div>
    <label>
        Color:
        <select on:change={updateColor} bind:value={color}>
            <option value="" disabled>Select color</option>
            {#each colors as col}
                <option value={col}>{col}</option>
            {/each}
        </select>
    </label>
    <label>
        Stroke Width:
        <select on:change={updateStrokeWidth} bind:value={strokeWidth}>
            <option value="" disabled>Select stroke width</option>
            {#each strokeWidths as sw}
                <option value={sw}>{sw}</option>
            {/each}
        </select>
    </label>
    <button on:click={deleteElement}>Delete Element</button>
</div>

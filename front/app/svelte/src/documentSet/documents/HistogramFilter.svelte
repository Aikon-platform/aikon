<script>
    /** [{key, total, part, title, label}]: `part` is filled in blue, `label` is html */
    export let bars;
    /** @type {Set} */
    export let selected;
    export let toggle;

    $: max = Math.max(...bars.map(b => b.total), 1);
</script>

<div class="columns is-gapless is-mobile mb-0" style="width: {2 * bars.length}rem; margin-top: -0.75em">
    {#each bars as {key, total, part, title, label}}
        <div class="column is-flex is-flex-direction-column is-justify-content-flex-end has-text-centered is-size-7 has-text-grey" style="height: 4rem">
            <button class="button is-small p-0 mx-1" {title} on:click={() => toggle(key)}
                    style="height: {5 + 70 * total / max}%; background: linear-gradient(to top, var(--bulma-link) {100 * part / (total || 1)}%, var(--bulma-border) 0); opacity: {!selected.size || selected.has(key) ? 1 : 0.4}"/>
            {@html label}
        </div>
    {/each}
</div>

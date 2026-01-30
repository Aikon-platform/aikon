<script>
    export let direction = ""; // 'left', 'right', 'up', 'down'

    export let delta = 0 // -1 or 1 for page navigation
    export let axis = null; // 'horizontal' or 'vertical'
    export let navigationFct = () => {}; // function to call on click
    export let css = ""; // additional css styles
    export let icon = "chevron";
    export let text = "";
</script>

<button class="nav-btn nav-{direction} is-flex is-flex-direction-column is-align-items-center"
        on:click={() => navigationFct(delta, axis)} aria-label="Navigate {direction}" style="{css}">
    {#if text}
        <span class="is-size-7 mb-1 has-text-grey">{text}</span>
    {/if}
    <span class="icon is-small p-0">
        <i class="fas fa-{icon}-{direction}"/>
    </span>
</button>

<style>
    .nav-btn {
        position: absolute;
        color: var(--bulma-link);
        cursor: pointer;
        z-index: 1;
    }

    .nav-up { top: 0; }
    .nav-down { bottom: 0; }
    .nav-left { left: 0; top: 50%; transform: translateY(-50%); }
    .nav-right { right: 0; top: 50%; transform: translateY(-50%); }
</style>

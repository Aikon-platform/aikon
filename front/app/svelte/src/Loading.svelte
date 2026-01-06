<script>
    import { fade } from 'svelte/transition';
    import {loading} from "./utils.js";
</script>

{#if $loading}
    <div class="bkg-shade" transition:fade="{{ duration: 150 }}">
        <div class="loader"/>
    </div>
{/if}

<style>
    .bkg-shade {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }

    .loader {
        border: 5px solid rgba(255, 255, 255, 0.5);
        border-top: 5px solid var(--bulma-link);
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>

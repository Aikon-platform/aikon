<script>
    import {slide} from 'svelte/transition';
    import TooltipGeneric from "./ui/TooltipGeneric.svelte";
    import {appLang} from "./constants.js";

    $: toolbarExpanded = false;
    let expandable = true;

    const toolbarText = {
        true: {
            en: "Collapse the toolbar",
            fr: "Refermer le menu"
        },
        false: {
            en: "Expand the toolbar",
            fr: "Ouvrir le menu"
        }
    }
    const toggleToolbarExpanded = () => toolbarExpanded = !toolbarExpanded;
</script>

<div id="toolbar" class="ctrl-wrapper is-flex is-justify-content-center is-align-items-center
     { toolbarExpanded ? 'toolbar-expanded' : 'toolbar-collapsed' }">

    <form class="ctrl">
        <div class="ctrl-base">
            <div class="ctrl-block-wrapper">
                <div class="ctrl-block">
                    <slot name="toolbar-visible"/>
                </div>
            </div>
        </div>
        {#if expandable}
            {#if toolbarExpanded}
                <div transition:slide={{axis: "y"}} class="ctrl-extra">
                    <slot name="toolbar-hidden"/>
                </div>
            {/if}
            <div class="ctrl-toggle">
                <button on:click|preventDefault={toggleToolbarExpanded} class="button is-link">
                    <svg style={`transform: rotate(${toolbarExpanded ? "180" : "0"}deg)`} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                        <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                              stroke-width="1.5" d="M12 3v18m0 0l8.5-8.5M12 21l-8.5-8.5"></path>
                    </svg>
                    <TooltipGeneric tooltipText={toolbarText[toolbarExpanded][appLang]}/>
                </button>
            </div>
        {/if}
    </form>
</div>

<style>
    #toolbar {
        top: var(--nav-actions-height);
    }

    .ctrl-wrapper {
        width: 100%;
        height: auto;
        position: sticky;
        background-color: var(--bulma-body-background-color);
        z-index: 2;
        margin: 0 0 max(10vh, 150px);
    }

    .ctrl {
        position: absolute;
        top: 0;
        width: 100%;
        background-color: var(--bulma-body-background-color);
        border: solid 1px var(--bulma-border);
        border-radius: 0 0 var(--bulma-burger-border-radius) var(--bulma-burger-border-radius);
        box-shadow: 0 3px;
        display: flex;
        flex-direction: column;
    }

    .toolbar-collapsed .ctrl {
        box-shadow: none;
    }

    .toolbar-expanded .ctrl {
        box-shadow: none;
    }

    .ctrl-block-wrapper {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border-bottom: solid 1px var(--bulma-border);
    }

    .ctrl-block {
        width: 70%;
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: space-around;
        margin: 5px;
    }

    .ctrl-toggle {
        height: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .ctrl-toggle > button {
        border: var(--default-border);
        border-radius: 2rem;
        height: 40px;
        width: 40px;
        position: relative;
    }

    .ctrl-toggle > button svg {
        height: 100%;
        transition: transform .5s;
    }
</style>
